"""
Financial Risk Assessment System
XGBoost + TreeSHAP + constrained DiCE (dual-layer explainable credit risk framework)

MSc dissertation, Baze University, Abuja: "Explainable Artificial Intelligence in Financial
Risk Prediction: A Dual-Layer Framework for Stable and Actionable Counterfactuals"
Author: Jamal E.O. Obaseki

Every file this app loads is written by XAI_Risk_Prediction_Notebook.ipynb (Step 22), so the
app, the notebook and the dissertation all use the same model, WoE scores and rules.
"""
import json
import os
import random

import dice_ml
import joblib
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import shap
import streamlit as st
from dice_ml import Dice
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

st.set_page_config(page_title="Financial Risk Assessment System", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
  .block-container {padding-top: 1.5rem;}
  h1 {color: #1e3a8a; font-weight: 700; margin-bottom: 0.2rem;}
  .subtitle {color: #475569; font-size: 1.05rem; margin-bottom: 1.2rem;}
  .section {background: #1e3a8a; color: white; padding: 0.6rem 1rem; border-radius: 6px; margin: 1.4rem 0 0.8rem 0; font-weight: 600;}
  .card {background: white; padding: 1rem 1.2rem; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 0.6rem;}
  .approved {color: #15803d; font-weight: 700;}
  .rejected {color: #b91c1c; font-weight: 700;}
  .small {color: #475569; font-size: 0.85rem;}
</style>
""", unsafe_allow_html=True)

RANDOM_STATE = 42
CODE_TEXT = {-9: "-9 = no bureau record", -8: "-8 = no usable or valid trades/inquiries", -7: "-7 = condition not met (e.g. never late, no recent inquiry)"}

FEATURES = {
    # name: (label, group, description, max value)
    "ExternalRiskEstimate": ("External risk estimate", "Credit history", "Consolidated risk score from the credit bureau (higher is better).", 100),
    "MSinceOldestTradeOpen": ("Months since oldest account opened", "Credit history", "How long ago the oldest credit account was opened.", 900),
    "MSinceMostRecentTradeOpen": ("Months since newest account opened", "Credit history", "How long ago the most recent credit account was opened.", 400),
    "AverageMInFile": ("Average months in file", "Credit history", "Average age of all credit accounts, in months.", 400),
    "NumSatisfactoryTrades": ("Satisfactory accounts", "Credit history", "Number of accounts in good standing.", 100),
    "NumTotalTrades": ("Total accounts", "Credit history", "Total number of credit accounts on file.", 120),
    "NumTradesOpeninLast12M": ("Accounts opened in last 12 months", "Credit history", "New credit accounts opened in the past year.", 30),
    "PercentInstallTrades": ("Percent instalment accounts", "Credit history", "Share of accounts that are instalment loans (0 to 100).", 100),
    "PercentTradesNeverDelq": ("Percent never late", "Delinquency history", "Share of accounts that have never been late (0 to 100).", 100),
    "NumTrades60Ever2DerogPubRec": ("Accounts ever 60+ days late", "Delinquency history", "Accounts ever 60 or more days late, or with a derogatory public record.", 30),
    "NumTrades90Ever2DerogPubRec": ("Accounts ever 90+ days late", "Delinquency history", "Accounts ever 90 or more days late, or with a derogatory public record.", 30),
    "MSinceMostRecentDelq": ("Months since last late payment", "Delinquency history", "Months since the most recent late payment.", 100),
    "MaxDelq2PublicRecLast12M": ("Worst delinquency, last 12 months (code)", "Delinquency history", "Bureau code for the worst delinquency in the last 12 months (0 to 9).", 9),
    "MaxDelqEver": ("Worst delinquency ever (code)", "Delinquency history", "Bureau code for the worst delinquency ever (2 to 8).", 9),
    "MSinceMostRecentInqexcl7days": ("Months since last credit inquiry", "Credit inquiries", "Months since the most recent credit check, ignoring the last 7 days (0 to 24).", 24),
    "NumInqLast6M": ("Inquiries in last 6 months", "Credit inquiries", "Number of credit checks in the last 6 months.", 70),
    "NumInqLast6Mexcl7days": ("Inquiries in last 6 months (excl. last 7 days)", "Credit inquiries", "Credit checks in the last 6 months, ignoring the last 7 days.", 70),
    "NetFractionRevolvingBurden": ("Revolving balance ratio (%)", "Balances and utilisation", "Card and revolving balances divided by their limits, in percent.", 250),
    "NetFractionInstallBurden": ("Instalment balance ratio (%)", "Balances and utilisation", "Instalment balances divided by the original loan amounts, in percent.", 500),
    "NumRevolvingTradesWBalance": ("Revolving accounts with a balance", "Balances and utilisation", "Number of cards or revolving accounts that carry a balance.", 40),
    "NumInstallTradesWBalance": ("Instalment accounts with a balance", "Balances and utilisation", "Number of instalment loans that still carry a balance.", 30),
    "NumBank2NatlTradesWHighUtilization": ("Bank/national accounts with high use", "Balances and utilisation", "Bank or national cards used above 75% of their limit.", 20),
    "PercentTradesWBalance": ("Percent accounts with a balance", "Balances and utilisation", "Share of all accounts that carry a balance (0 to 100).", 100),
}
FEATURE_ORDER = ["ExternalRiskEstimate", "MSinceOldestTradeOpen", "MSinceMostRecentTradeOpen", "AverageMInFile",
                 "NumSatisfactoryTrades", "NumTrades60Ever2DerogPubRec", "NumTrades90Ever2DerogPubRec",
                 "PercentTradesNeverDelq", "MSinceMostRecentDelq", "MaxDelq2PublicRecLast12M", "MaxDelqEver",
                 "NumTotalTrades", "NumTradesOpeninLast12M", "PercentInstallTrades", "MSinceMostRecentInqexcl7days",
                 "NumInqLast6M", "NumInqLast6Mexcl7days", "NetFractionRevolvingBurden", "NetFractionInstallBurden",
                 "NumRevolvingTradesWBalance", "NumInstallTradesWBalance", "NumBank2NatlTradesWHighUtilization",
                 "PercentTradesWBalance"]

EXAMPLES = {
    "Typical applicant (median values)": {"ExternalRiskEstimate": 72, "MSinceOldestTradeOpen": 186, "MSinceMostRecentTradeOpen": 6,
        "AverageMInFile": 76, "NumSatisfactoryTrades": 20, "NumTrades60Ever2DerogPubRec": 0, "NumTrades90Ever2DerogPubRec": 0,
        "PercentTradesNeverDelq": 97, "MSinceMostRecentDelq": -7, "MaxDelq2PublicRecLast12M": 6, "MaxDelqEver": 6,
        "NumTotalTrades": 21, "NumTradesOpeninLast12M": 1, "PercentInstallTrades": 33, "MSinceMostRecentInqexcl7days": 0,
        "NumInqLast6M": 1, "NumInqLast6Mexcl7days": 1, "NetFractionRevolvingBurden": 29, "NetFractionInstallBurden": 74,
        "NumRevolvingTradesWBalance": 3, "NumInstallTradesWBalance": 2, "NumBank2NatlTradesWHighUtilization": 1,
        "PercentTradesWBalance": 67},
    "Test applicant 8347 (rejected; realistic options exist)": {"ExternalRiskEstimate": 72, "MSinceOldestTradeOpen": 199,
        "MSinceMostRecentTradeOpen": 0, "AverageMInFile": 84, "NumSatisfactoryTrades": 15, "NumTrades60Ever2DerogPubRec": 1,
        "NumTrades90Ever2DerogPubRec": 1, "PercentTradesNeverDelq": 94, "MSinceMostRecentDelq": 35, "MaxDelq2PublicRecLast12M": 6,
        "MaxDelqEver": 2, "NumTotalTrades": 19, "NumTradesOpeninLast12M": 3, "PercentInstallTrades": 47,
        "MSinceMostRecentInqexcl7days": 0, "NumInqLast6M": 3, "NumInqLast6Mexcl7days": 3, "NetFractionRevolvingBurden": 10,
        "NetFractionInstallBurden": -8, "NumRevolvingTradesWBalance": 4, "NumInstallTradesWBalance": -8,
        "NumBank2NatlTradesWHighUtilization": 0, "PercentTradesWBalance": 56},
    "Test applicant 6470 (rejected; no realistic option)": {"ExternalRiskEstimate": 51, "MSinceOldestTradeOpen": 162,
        "MSinceMostRecentTradeOpen": 35, "AverageMInFile": 73, "NumSatisfactoryTrades": 4, "NumTrades60Ever2DerogPubRec": 1,
        "NumTrades90Ever2DerogPubRec": 1, "PercentTradesNeverDelq": 50, "MSinceMostRecentDelq": 1, "MaxDelq2PublicRecLast12M": 2,
        "MaxDelqEver": 4, "NumTotalTrades": 6, "NumTradesOpeninLast12M": 0, "PercentInstallTrades": 33,
        "MSinceMostRecentInqexcl7days": 0, "NumInqLast6M": 0, "NumInqLast6Mexcl7days": 0, "NetFractionRevolvingBurden": 43,
        "NetFractionInstallBurden": 11, "NumRevolvingTradesWBalance": 1, "NumInstallTradesWBalance": 1,
        "NumBank2NatlTradesWHighUtilization": 0, "PercentTradesWBalance": 50},
}


# ------------------------------------------------------------------ loading
class WoETransformer(BaseEstimator, TransformerMixin):
    """Replaces the special codes -7, -8, -9 with their Weight of Evidence scores (same as the notebook)."""
    def __init__(self, woe_map):
        self.woe_map = woe_map

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = pd.DataFrame(X, columns=FEATURE_ORDER).astype(float).copy()
        for col, codes in self.woe_map.items():
            for code, w in codes.items():
                X.loc[X[col] == code, col] = w
        return X


@st.cache_resource
def load_artifacts():
    missing = [f for f in ["model.pkl", "woe_map.json", "actionability_rules.json", "dice_background.csv", "metrics.json"] if not os.path.exists(f)]
    if missing:
        return None, missing
    model = joblib.load("model.pkl")
    woe_map = {c: {int(k): v for k, v in d.items()} for c, d in json.load(open("woe_map.json")).items()}
    rules_file = json.load(open("actionability_rules.json"))
    pipe = Pipeline([("woe", WoETransformer(woe_map)), ("xgb", model)])
    explainer = shap.TreeExplainer(model)
    background = pd.read_csv("dice_background.csv")
    d = dice_ml.Data(dataframe=background, continuous_features=FEATURE_ORDER, outcome_name="Target")
    dice = Dice(d, dice_ml.Model(model=pipe, backend="sklearn"), method="genetic")
    metrics = json.load(open("metrics.json"))
    exp_metrics = json.load(open("exp_metrics.json")) if os.path.exists("exp_metrics.json") else {}
    return {"model": model, "woe_map": woe_map, "pipe": pipe, "explainer": explainer, "dice": dice,
            "rules": rules_file["rules"], "horizon": rules_file["horizon_months"], "metrics": metrics,
            "exp_metrics": exp_metrics, "background": background}, []


def action_bounds(row, rules, horizon):
    vary, ranges = [], {}
    for f, rule in rules.items():
        v = row[f]
        if rule == "fixed" or v < 0:
            continue
        lo, hi = {"up_time": (v, v + horizon), "up_time_24": (v, min(v + horizon, 24)),
                  "up_to_total": (v, max(v, row["NumTotalTrades"])), "down": (0, v)}[rule]
        if hi > lo:
            vary.append(f)
            ranges[f] = [int(lo), int(hi)]
    return vary, ranges


def describe_change(f, old, new):
    label = FEATURES[f][0]
    if new < old:
        return f"Lower **{label}** from {old} to {new}"
    if f.startswith("MSince") or f == "AverageMInFile":
        return f"Let **{label}** grow from {old} to {new} (about {new - old} more months without new negative events)"
    return f"Raise **{label}** from {old} to {new}"


A, missing = load_artifacts()
st.markdown("<h1>Financial Risk Assessment System</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>XGBoost predictor with a TreeSHAP and constrained DiCE explanation layer, trained on the FICO HELOC data</p>", unsafe_allow_html=True)
if A is None:
    st.error("Missing file(s): " + ", ".join(missing) + ". Run XAI_Risk_Prediction_Notebook.ipynb to the end (Step 22) and place its outputs next to app.py.")
    st.stop()

M, E = A["metrics"], A["exp_metrics"]
with st.sidebar:
    st.markdown("### About this system")
    st.markdown(f"""
**Prediction layer**
- XGBoost, tuned with Optuna (TPE, 20 trials)
- Test AUC-ROC: **{M['auc']:.4f}**
- Gini: **{M['gini']:.4f}** | KS: **{M['ks']:.4f}**

**Explanation layer**
- TreeSHAP reasons for every decision
- Constrained DiCE options for rejected applicants (whole numbers, fixed history, 24-month horizon)

**Research context**
- MSc dissertation, Baze University, Abuja
- Jamal E.O. Obaseki
""")
    st.markdown("---")
    page = st.radio("Select page", ["Risk Assessment", "Model Performance", "Documentation"])

# ------------------------------------------------------------------ page 1
if page == "Risk Assessment":
    st.markdown("<div class='section'>Applicant information</div>", unsafe_allow_html=True)
    st.write("Enter the applicant's credit bureau values. Whole numbers only. Where the bureau reports a special code, enter it: "
             + "; ".join(CODE_TEXT.values()) + ".")
    def load_example():
        for f, v in EXAMPLES[st.session_state["example"]].items():
            st.session_state[f] = int(v)
    if "ExternalRiskEstimate" not in st.session_state:
        for f, v in EXAMPLES["Typical applicant (median values)"].items():
            st.session_state[f] = int(v)
    st.selectbox("Start from an example (optional)", list(EXAMPLES.keys()), key="example", on_change=load_example)
    with st.form("applicant_form"):
        values = {}
        for group in ["Credit history", "Delinquency history", "Credit inquiries", "Balances and utilisation"]:
            st.markdown(f"#### {group}")
            feats = [f for f in FEATURE_ORDER if FEATURES[f][1] == group]
            cols = st.columns(3)
            for j, f in enumerate(feats):
                label, _, desc, mx = FEATURES[f]
                with cols[j % 3]:
                    values[f] = st.number_input(label, min_value=-9, max_value=mx, step=1, help=desc, key=f)
        submitted = st.form_submit_button("Assess risk", type="primary", width="stretch")

    if submitted:
        bad = [FEATURES[f][0] for f, v in values.items() if v < 0 and v not in (-7, -8, -9)]
        if bad:
            st.error("Negative values are only allowed as the bureau codes -7, -8 or -9. Please check: " + ", ".join(bad))
            st.stop()
        raw = pd.DataFrame([values])[FEATURE_ORDER]
        p_bad = float(A["pipe"].predict_proba(raw)[0, 1])
        rejected = p_bad >= 0.5

        st.markdown("<div class='section'>Decision</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Decision", "REJECTED" if rejected else "APPROVED")
        c1.markdown("<span class='rejected'>Predicted to default (P(Bad) at or above 0.50)</span>" if rejected else
                    "<span class='approved'>Predicted to repay (P(Bad) below 0.50)</span>", unsafe_allow_html=True)
        c2.metric("Probability of default, P(Bad)", f"{p_bad:.1%}")
        c2.progress(min(max(p_bad, 0.0), 1.0))
        band = "Low" if p_bad < 0.3 else "Moderate" if p_bad < 0.5 else "High" if p_bad < 0.7 else "Very high"
        c3.metric("Risk band", band)
        c3.markdown("<span class='small'>Bands: low below 30%, moderate 30 to 50%, high 50 to 70%, very high 70% and above.</span>", unsafe_allow_html=True)

        st.markdown("<div class='section'>Why the model decided this (TreeSHAP)</div>", unsafe_allow_html=True)
        x_model = A["pipe"].named_steps["woe"].transform(raw)
        sv = pd.Series(A["explainer"].shap_values(x_model)[0], index=FEATURE_ORDER)
        top = sv.reindex(sv.abs().sort_values(ascending=False).index).head(8)
        fig = go.Figure(go.Bar(x=top.values[::-1], y=[f"{FEATURES[f][0]} = {values[f]}" for f in top.index[::-1]], orientation="h",
                               marker_color=["#b91c1c" if v > 0 else "#15803d" for v in top.values[::-1]],
                               hovertemplate="%{y}<br>SHAP %{x:+.3f}<extra></extra>"))
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=10, b=10), xaxis_title="SHAP value (log-odds): right raises risk, left lowers risk",
                          plot_bgcolor="white")
        fig.add_vline(x=0, line_color="#334155", line_width=1)
        st.plotly_chart(fig, width="stretch")
        st.caption(f"The SHAP values add up exactly to the model's score for this applicant: base value {float(A['explainer'].expected_value):.3f} "
                   f"+ sum of SHAP values {sv.sum():+.3f} = {float(A['explainer'].expected_value) + sv.sum():.3f} log-odds.")

        if rejected:
            st.markdown("<div class='section'>What could change the decision (constrained DiCE)</div>", unsafe_allow_html=True)
            vary, ranges = action_bounds(raw.iloc[0], A["rules"], A["horizon"])
            st.write("Only realistic changes are searched: past late payments, the bureau score and the account mix stay fixed, "
                     f"time can only move forward (up to {A['horizon']} months), and balances, new accounts and inquiries can only go down.")
            with st.spinner("Searching for realistic options (about 10 to 20 seconds)..."):
                np.random.seed(RANDOM_STATE); random.seed(RANDOM_STATE)
                cfs = None
                if vary:
                    try:
                        res = A["dice"].generate_counterfactuals(raw, total_CFs=3, desired_class=0, features_to_vary=vary,
                                                                 permitted_range=ranges, proximity_weight=0.5, diversity_weight=0.5, verbose=False)
                        cfs = res.cf_examples_list[0].final_cfs_df
                    except Exception:
                        cfs = None
            if cfs is None or len(cfs) == 0:
                best = raw.iloc[0].astype(float).copy()
                for f in vary:
                    best[f] = ranges[f][0] if A["rules"][f] == "down" else ranges[f][1]
                p_best = float(A["pipe"].predict_proba(best.to_frame().T)[0, 1]) if vary else p_bad
                st.warning(f"No realistic option was found. Even if every allowed change were made at once, the predicted probability of default "
                           f"would be {p_best:.1%}, which is still at or above the 50% cut-off. Under these rules this applicant cannot become "
                           f"approvable within {A['horizon']} months; the reasons above show what is driving the risk.")
            else:
                cfs = cfs[FEATURE_ORDER].astype(int)
                for k in range(len(cfs)):
                    c = cfs.iloc[k]
                    p_new = float(A["pipe"].predict_proba(c.to_frame().T)[0, 1])
                    changes = [describe_change(f, int(values[f]), int(c[f])) for f in FEATURE_ORDER if int(c[f]) != int(values[f])]
                    st.markdown(f"<div class='card'><b>Option {k + 1}</b> (P(Bad) would fall from {p_bad:.1%} to {p_new:.1%})</div>", unsafe_allow_html=True)
                    for ch in changes:
                        st.markdown(f"- {ch}")
                st.caption("Each option was fed back into the model and checked. Options are suggestions from the model, not financial advice.")

# ------------------------------------------------------------------ page 2
elif page == "Model Performance":
    st.markdown("<div class='section'>Prediction quality on the held-out test set (2,092 applicants)</div>", unsafe_allow_html=True)
    cols = st.columns(4)
    cols[0].metric("AUC-ROC", f"{M['auc']:.4f}")
    cols[1].metric("Gini", f"{M['gini']:.4f}")
    cols[2].metric("KS statistic", f"{M['ks']:.4f}")
    cols[3].metric("Accuracy", f"{M['acc']:.4f}")
    cols = st.columns(4)
    cols[0].metric("Precision", f"{M['prec']:.4f}")
    cols[1].metric("Recall", f"{M['rec']:.4f}")
    cols[2].metric("F1-score", f"{M['f1']:.4f}")
    if "auc_ci_low" in M:
        cols[3].metric("AUC 95% bootstrap interval", f"{M['auc_ci_low']:.3f} to {M['auc_ci_high']:.3f}")
    if E:
        st.markdown("<div class='section'>Counterfactual and stability quality</div>", unsafe_allow_html=True)
        cols = st.columns(4)
        cols[0].metric("Validity", f"{E['validity']:.0%}", help="Share of produced counterfactuals that really flip the decision.")
        cols[1].metric("Coverage", f"{E['coverage']:.0%}", help="Share of the 10 rejected test applicants who received at least one option.")
        cols[2].metric("Rule compliance", f"{E['rule_compliance']:.0%}", help="Share of options that obey every actionability rule.")
        cols[3].metric("Sparsity", f"{E['sparsity']:.2f} features", help="Average number of features each option changes.")
        cols = st.columns(4)
        cols[0].metric("Proximity (L1, raw)", f"{E['proximity']:.2f}")
        cols[1].metric("Proximity (MAD-scaled)", f"{E['proximity_mad']:.2f}")
        if "cf_stability_seed" in E:
            cols[2].metric("Advice stability (other seeds)", f"{E['cf_stability_seed']:.2f}", help="Mean Jaccard overlap of the features named in the advice.")
        if "prediction_stability_whole_0.10sd" in E:
            cols[3].metric("Decisions unchanged (0.10 SD noise)", f"{E['prediction_stability_whole_0.10sd']:.1%}")
    figs = [("figures/fig_roc.png", "ROC curve"), ("figures/fig_confusion.png", "Confusion matrix"),
            ("figures/fig_shap_importance.png", "Global TreeSHAP importance"), ("figures/fig_baselines.png", "Baseline comparison")]
    present = [(p, c) for p, c in figs if os.path.exists(p)]
    for j in range(0, len(present), 2):
        cols = st.columns(2)
        for col, (p, c) in zip(cols, present[j:j + 2]):
            col.image(p, caption=c, width="stretch")

# ------------------------------------------------------------------ page 3
else:
    st.markdown("<div class='section'>System documentation</div>", unsafe_allow_html=True)
    st.markdown(f"""
### What the system does
1. **Predicts** the chance that an applicant will fall 90 or more days behind (P(Bad)). Applicants at or above 0.50 are rejected.
2. **Explains** every decision with TreeSHAP: the exact contribution of each of the 23 features.
3. **Advises** rejected applicants with up to three constrained counterfactual options from DiCE's genetic search.

### How the data is prepared
- Special bureau codes (-9, -8, -7) are replaced by their Weight of Evidence scores; real values are left as they are.
- The model was trained on 8,734 rows (the 8,367 training applicants plus 367 synthetic rows from SMOTE) and tested on 2,092 untouched applicants.

### Model settings (found by Optuna)
max_depth = 4, learning_rate = 0.0281, n_estimators = 300, subsample = 0.7728, colsample_bytree = 0.7165.

### Actionability rules used for advice
- **Fixed:** external risk estimate, past late payments (60+ and 90+ day counts, worst delinquency ever and in the last 12 months, percent never late), total accounts and account mix.
- **Time moves forward only** (up to {A['horizon']} months): account ages and months since the last late payment, new account and inquiry.
- **Can only go down:** balances, utilisation, accounts with balances, new accounts in the last 12 months and recent inquiries.
- A feature holding a special code is never changed. All suggestions are whole numbers.

### Known limits
- Features that move together in real life (for example, time passing ages every account) are searched separately.
- Some rejected applicants have no realistic option within the horizon; the app says so instead of inventing one.
- The data is a US home-equity product; results may not transfer to other products or countries without retraining.

### Key methodological sources
- Lundberg, S. M., et al. (2020). From local explanations to global understanding with explainable AI for trees. *Nature Machine Intelligence, 2*(1), 56-67.
- Mothilal, R. K., Sharma, A., & Tan, C. (2020). Explaining machine learning classifiers through diverse counterfactual explanations. *Proceedings of FAT\\* 2020*, 607-617.
- Bentéjac, C., Csörgő, A., & Martínez-Muñoz, G. (2021). A comparative analysis of gradient boosting algorithms. *Artificial Intelligence Review, 54*(3), 1937-1967.
- Karimi, A.-H., Barthe, G., Schölkopf, B., & Valera, I. (2023). A survey of algorithmic recourse. *ACM Computing Surveys, 55*(5), Article 95.
- Kothari, A., Kulynych, B., Weng, T.-W., & Ustun, B. (2024). Prediction without preclusion: Recourse verification with reachable sets. *ICLR 2024*.

**Dissertation:** Explainable Artificial Intelligence in Financial Risk Prediction: A Dual-Layer Framework for Stable and Actionable Counterfactuals.
**Author:** Jamal E.O. Obaseki | **Institution:** Baze University, Abuja | **Department:** Computer Science (MSc)
""")

st.markdown("---")
st.markdown("<div style='text-align:center; color:#64748b; font-size:0.85rem;'>Financial Risk Assessment System | XGBoost + TreeSHAP + constrained DiCE | "
            "Baze University, Abuja | For research and education; not for live lending decisions without independent validation.</div>",
            unsafe_allow_html=True)
