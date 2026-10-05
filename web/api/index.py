"""Vercel API: original XGBoost model, native TreeSHAP, original constrained DiCE.

The JSON model is a portable export of ../model.pkl, not a retrained model.
Input profiles are processed in memory and are never written to disk or logs.
"""
import json
import math
import os
import random
import sys
import threading
from functools import lru_cache
from http.server import BaseHTTPRequestHandler
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"
sys.path.insert(0, str(ARTIFACTS.parent / "vendor"))
CONFIG = json.loads((ARTIFACTS / "config.json").read_text())
ORDER = CONFIG["order"]
WOE = json.loads((ARTIFACTS / "woe_map.json").read_text())
RULES_FILE = json.loads((ARTIFACTS / "actionability_rules.json").read_text())
LOCK = threading.Lock()


class WoETransformer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = pd.DataFrame(X, columns=ORDER).astype(float).copy()
        for feature, codes in WOE.items():
            for code, weight in codes.items():
                X.loc[X[feature] == int(code), feature] = weight
        return X


@lru_cache(maxsize=1)
def get_model():
    model = xgb.XGBClassifier(n_jobs=1)
    model.load_model(ARTIFACTS / "model.json")
    model.set_params(n_jobs=1)
    return model


def validate(values):
    if not isinstance(values, dict) or set(values) != set(ORDER):
        raise ValueError("Please supply all 23 credit values.")
    cleaned = {}
    for feature in ORDER:
        value = values[feature]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{CONFIG['features'][feature]['label']}: enter a whole number.")
        if not math.isfinite(value) or int(value) != value:
            raise ValueError(f"{CONFIG['features'][feature]['label']}: enter a whole number.")
        if value < 0 and value not in (-7, -8, -9):
            raise ValueError("Use a recorded value, or choose one of the three missing-record codes.")
        if value > CONFIG['features'][feature]['max']:
            raise ValueError(f"{CONFIG['features'][feature]['label']}: this value is above the allowed range.")
        cleaned[feature] = int(value)
    return cleaned


def predict(values):
    raw = pd.DataFrame([validate(values)], columns=ORDER)
    transformed = WoETransformer().transform(raw)
    model = get_model()
    probability = float(model.predict_proba(transformed)[0, 1])
    # XGBoost's exact tree-path-dependent TreeSHAP uses the trained tree covers,
    # matching TreeExplainer(model) in the original Streamlit app.
    contributions = model.get_booster().predict(xgb.DMatrix(transformed), pred_contribs=True)[0]
    return {
        "probability": probability,
        "higher_risk": probability >= 0.5,
        "band": "Low" if probability < 0.3 else "Moderate" if probability < 0.5 else "High" if probability < 0.7 else "Very high",
        "threshold": 0.5,
        "base_value": float(contributions[-1]),
        "reasons": sorted([
            {"feature": feature, "value": int(raw.iloc[0][feature]), "contribution": float(contributions[i])}
            for i, feature in enumerate(ORDER)
        ], key=lambda reason: abs(reason['contribution']), reverse=True),
    }


def action_bounds(values):
    vary, ranges = [], {}
    horizon = RULES_FILE['horizon_months']
    for feature, rule in RULES_FILE['rules'].items():
        value = values[feature]
        if rule == "fixed" or value < 0:
            continue
        lo, hi = {
            "up_time": (value, value + horizon),
            "up_time_24": (value, min(value + horizon, 24)),
            "up_to_total": (value, max(value, values['NumTotalTrades'])),
            "down": (0, value),
        }[rule]
        hi = min(hi, CONFIG['features'][feature]['max'])
        if hi > lo:
            vary.append(feature)
            ranges[feature] = [int(lo), int(hi)]
    return vary, ranges


def valid_option(original, candidate, ranges):
    for feature in ORDER:
        value = float(candidate[feature])
        if not math.isfinite(value) or value != round(value):
            return False
        if feature not in ranges:
            if value != original[feature]:
                return False
        elif not ranges[feature][0] <= value <= ranges[feature][1]:
            return False
    return True


def options(values):
    values = validate(values)
    original_result = predict(values)
    if not original_result['higher_risk']:
        return {"options": [], "status": "already_below_threshold", "horizon_months": 24}
    vary, ranges = action_bounds(values)
    if not vary:
        return {"options": [], "status": "no_changeable_values", "horizon_months": 24}
    # Each search owns its explainer. The lock protects DiCE's global random seed.
    with LOCK:
        import dice_ml
        from raiutils.exceptions import UserConfigValidationException
        np.random.seed(42)
        random.seed(42)
        background = pd.read_csv(ARTIFACTS / "dice_background.csv")
        pipe = Pipeline([("woe", WoETransformer()), ("xgb", get_model())])
        data = dice_ml.Data(dataframe=background, continuous_features=ORDER, outcome_name="Target")
        dice = dice_ml.Dice(data, dice_ml.Model(model=pipe, backend="sklearn"), method="genetic")
        try:
            result = dice.generate_counterfactuals(
                pd.DataFrame([values], columns=ORDER), total_CFs=3, desired_class=0,
                features_to_vary=vary, permitted_range=ranges,
                proximity_weight=0.5, diversity_weight=0.5, verbose=False,
            )
        except UserConfigValidationException as error:
            if 'No counterfactuals found for any of the query points!' in str(error):
                return {"options": [], "status": "not_found", "horizon_months": 24}
            raise
        candidates = result.cf_examples_list[0].final_cfs_df
    accepted, seen = [], set()
    if candidates is not None:
        for _, candidate in candidates.iterrows():
            if not valid_option(values, candidate, ranges):
                continue
            profile = {feature: int(candidate[feature]) for feature in ORDER}
            key = tuple(profile[feature] for feature in ORDER)
            if key in seen:
                continue
            seen.add(key)
            new_probability = predict(profile)['probability']
            if new_probability >= 0.5:
                continue
            accepted.append({"probability": new_probability, "values": profile,
                "changes": [{"feature": feature, "old": values[feature], "new": profile[feature]}
                    for feature in ORDER if profile[feature] != values[feature]]})
    # Failure to find a solution is not a mathematical proof of impossibility.
    return {"options": accepted, "status": "found" if accepted else "not_found", "horizon_months": 24}


class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        body = json.dumps(payload, allow_nan=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.respond(200, {"status": "ready", "model": "original-xgboost", "features": len(ORDER)})

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384:
                return self.respond(413, {"error": "This request is too large or empty."})
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Please send a credit profile.")
            operation = body.get('operation', 'predict')
            if operation not in ('predict', 'options'):
                raise ValueError("Choose a risk assessment or an options search.")
            output = predict(body.get('values')) if operation == 'predict' else options(body.get('values'))
            self.respond(200, output)
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self.respond(400, {"error": str(error)})
        except Exception:
            self.respond(503, {"error": "The model could not finish this request. Please try again shortly."})
