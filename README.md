# XAI Risk Prediction: XGBoost + TreeSHAP + constrained DiCE

Code for the MSc dissertation *Explainable Artificial Intelligence in Financial Risk Prediction: A Dual-Layer Framework for Stable and Actionable Counterfactuals* (Jamal E.O. Obaseki, Baze University, Abuja).

## Clarity website

The new Vercel website is in [`web/`](web/). It offers a four-section assessment,
three ready-to-use profiles, exact TreeSHAP reasons, on-demand constrained DiCE
options, the original research figures, light/dark themes and a five-stage
presentation mode. Inputs are processed in memory; the application does not
persist applicant profiles. Reports can be saved through the browser's PDF print dialog.

The website uses a portable JSON export of the existing `model.pkl`. It was
checked against the original model on all 10,459 dataset profiles: every
predicted probability matched exactly. The original Streamlit app and notebook
remain available below.

### Preview the website

```bash
python3.12 -m venv website-venv
source website-venv/bin/activate
pip install -r web/requirements.txt
python web/scripts/serve.py
```

Open http://localhost:3000. To run the model checks:

```bash
python -m unittest discover -s web/tests -v
```

### Deploy to Vercel

Import this repository, set the root directory to `web`, select **Other** as the
framework, and use `public` as the output directory. `web/vercel.json` configures
the static frontend and Python API. No API keys or database are required.
DiCE 0.12 is vendored with its MIT licence so its dependency metadata does not
install a separate GPU XGBoost package alongside the CPU runtime.

The counterfactual endpoint runs the same genetic search with the original
rules and seed 42. Returned options are checked for whole numbers, fixed fields,
allowed ranges and a probability below 50%. Input bounds from the existing app
also cap the search ranges. A search with no result is reported as “not found”;
it is not presented as proof that an improvement is impossible.

## What is in this repository

| File | Purpose |
|---|---|
| `XAI_Risk_Prediction_Notebook.ipynb` | The full modelling pipeline with every output saved: data, WoE, SMOTE, baselines, Optuna tuning, evaluation, DeLong tests, TreeSHAP, constrained DiCE, stability tests, timings |
| `app.py` | Streamlit web app (prediction, TreeSHAP reasons, constrained DiCE options) |
| `heloc_dataset_v1.csv` | FICO HELOC data (10,459 applicants, 23 features); the notebook also accepts the existing name `heloc_dataset_v1 (1).csv` |
| `model.pkl` | Trained XGBoost model (written by notebook Step 8) |
| `woe_map.json` | Weight of Evidence score for every special code (Step 22) |
| `actionability_rules.json` | Rules that limit counterfactual changes, and the 24-month horizon (Step 22) |
| `dice_background.csv` | Real training applicants in raw units, used by DiCE (Step 22) |
| `metrics.json`, `exp_metrics.json` | Test-set scores and counterfactual/stability scores (Steps 9, 17, 20) |
| `figures/` | Every chart produced by the notebook |
| `requirements.txt` | Packages for the web app |
| `requirements-notebook.txt` | Exact package versions used to run the notebook |

`README_DEPLOYMENT.md` from the earlier version is out of date (it names a file that does not exist) and can be deleted.

## Reproduce the results

```bash
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements-notebook.txt
jupyter nbconvert --to notebook --execute XAI_Risk_Prediction_Notebook.ipynb
```

With these versions and seed 42, the run rebuilds the original model exactly (test AUC 0.7933, Gini 0.5865, KS 0.4433).

## Run the web app locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Deploy on Streamlit Community Cloud

1. Push this repository to GitHub (all files above must be in the root).
2. At share.streamlit.io choose **New app**, select this repository, branch `main`, main file `app.py`.
3. Under **Advanced settings** choose **Python 3.11**, then **Deploy**.

## Pages in the app

1. **Risk Assessment**: enter the 23 bureau values (or load an example), get the decision, P(Bad), TreeSHAP reasons and, if rejected, up to three constrained counterfactual options or an honest "no realistic option" message.
2. **Model Performance**: test-set scores, counterfactual quality and stability scores, and the notebook figures.
3. **Documentation**: how the system works, the actionability rules and its known limits.

For research and education. Not for live lending decisions without independent validation.
