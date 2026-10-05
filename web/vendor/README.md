# DiCE 0.12

This directory contains the unmodified Python source package from the published
`dice-ml==0.12` wheel (https://github.com/interpretml/DiCE), under its MIT licence.
The licence is included in `DiCE License.txt`.

The source is vendored so that Vercel can use the small CPU-only XGBoost runtime.
The wheel's dependency metadata requires the separate `xgboost` distribution,
which would otherwise install an unnecessary GPU runtime alongside `xgboost-cpu`.
No search code, model behaviour, or DiCE algorithm was changed.
Runtime dependencies used by the sklearn genetic search are in `requirements.txt`.
