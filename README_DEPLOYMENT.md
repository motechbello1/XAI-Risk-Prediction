# Financial Risk Assessment System - Streamlit Deployment

## Quick Deployment to Streamlit Cloud

### 1. Upload Files to GitHub
Create a new repository with these files:
```
your-repo/
├── streamlit_app.py
├── requirements.txt
├── model.pkl (trained model from Colab)
├── metrics.json (from Colab)
└── exp_metrics.json (from Colab - optional)
```

### 2. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub repository
4. Select:
   - Repository: your-repo-name
   - Branch: main
   - Main file path: streamlit_app.py
5. Click "Deploy"

### 3. Your app will be live at:
```
https://share.streamlit.io/[your-username]/[your-repo]/main/streamlit_app.py
```

## Local Testing

### Run locally before deploying:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Open browser to:
```
http://localhost:8501
```

## File Requirements

### Essential Files:
- `streamlit_app.py` - Main application
- `requirements.txt` - Python dependencies
- `model.pkl` - Trained XGBoost model (from Colab notebook)

### Optional Files (for full functionality):
- `metrics.json` - Model performance metrics
- `exp_metrics.json` - Explainability quality metrics

## Features

### 3 Main Pages:
1. **Risk Assessment** - Input applicant data, get predictions + explanations
2. **Model Performance** - View metrics (AUC-ROC, Gini, etc.)
3. **Documentation** - System overview and research context

### Key Capabilities:
- Professional UI with clean design (no emojis)
- Detailed field descriptions under each input
- SHAP global explanations
- Counterfactual recommendations for rejected applicants
- Regulatory-compliant output format

## Customization

### Change Theme:
Create `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#3b82f6"
backgroundColor = "#f8f9fa"
secondaryBackgroundColor = "#ffffff"
textColor = "#1e3a8a"
font = "sans serif"
```

### Update Model:
Replace `model.pkl` with your latest trained model. Ensure it's an XGBoost classifier trained on the same features.

## Troubleshooting

### "Model file not found" error:
- Ensure `model.pkl` is in the same directory as `streamlit_app.py`
- Check file uploaded to GitHub repository

### Missing metrics:
- If `metrics.json` or `exp_metrics.json` are missing, the app will show warnings but still work
- These files are only needed for the "Model Performance" page

### Slow first load:
- First run downloads dependencies (~2-3 minutes)
- Subsequent runs are cached and load instantly

## Production Deployment

For production use:
1. Add authentication (Streamlit supports OAuth)
2. Connect to live database for applicant data
3. Implement audit logging for compliance
4. Add rate limiting for API protection
5. Set up monitoring and alerts

## Support

For issues or questions:
- Check Streamlit documentation: https://docs.streamlit.io
- Contact: Baze University, Department of Computer Science
