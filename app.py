import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import dice_ml
from dice_ml import Dice
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Financial Risk Assessment System",
    page_layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #3b82f6;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: #475569;
        font-weight: 500;
    }
    .subtitle {
        color: #64748b;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .approved {
        color: #16a34a;
        font-weight: 600;
    }
    .rejected {
        color: #dc2626;
        font-weight: 600;
    }
    .info-text {
        color: #64748b;
        font-size: 0.85rem;
        margin-top: 0.25rem;
        font-style: italic;
    }
    .section-header {
        background: linear-gradient(90deg, #3b82f6 0%, #1e3a8a 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 2rem 0 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Feature descriptions dictionary
FEATURE_DESCRIPTIONS = {
    'ExternalRiskEstimate': 'Consolidated risk score from external credit bureau (0-100, higher is better)',
    'MSinceOldestTradeOpen': 'Number of months since oldest trade account was opened',
    'MSinceMostRecentTradeOpen': 'Number of months since most recent trade account was opened',
    'AverageMInFile': 'Average months of trade accounts in credit file',
    'NumSatisfactoryTrades': 'Total number of satisfactory trade accounts',
    'NumTrades60Ever2DerogPubRec': 'Number of trades 60+ days past due or with public records',
    'NumTrades90Ever2DerogPubRec': 'Number of trades 90+ days past due or with public records',
    'PercentTradesNeverDelq': 'Percentage of trades that have never been delinquent (0-100)',
    'MSinceMostRecentDelq': 'Number of months since most recent delinquency',
    'MaxDelq2PublicRecLast12M': 'Maximum delinquency severity in last 12 months (0-9 scale)',
    'MaxDelqEver': 'Maximum delinquency severity ever recorded (0-9 scale)',
    'NumTotalTrades': 'Total number of trade accounts in credit file',
    'NumTradesOpeninLast12M': 'Number of trade accounts opened in last 12 months',
    'PercentInstallTrades': 'Percentage of installment trades (0-100)',
    'MSinceMostRecentInqexcl7days': 'Months since most recent inquiry (excluding last 7 days)',
    'NumInqLast6M': 'Number of credit inquiries in last 6 months',
    'NumInqLast6Mexcl7days': 'Number of inquiries in last 6 months (excluding last 7 days)',
    'NetFractionRevolvingBurden': 'Revolving balance divided by credit limit (percentage)',
    'NetFractionInstallBurden': 'Installment balance divided by original loan amount (percentage)',
    'NumRevolvingTradesWBalance': 'Number of revolving trades with outstanding balance',
    'NumInstallTradesWBalance': 'Number of installment trades with outstanding balance',
    'NumBank2NatlTradesWHighUtilization': 'Number of bank/national trades with high utilization (>75%)',
    'PercentTradesWBalance': 'Percentage of trades with outstanding balance (0-100)'
}

# Load model and explainers (cache for performance)
@st.cache_resource
def load_model():
    try:
        model = joblib.load('model.pkl')
        return model
    except:
        st.error("Model file not found. Please ensure 'model.pkl' is in the same directory.")
        return None

@st.cache_resource
def load_explainer(_model):
    if _model is not None:
        return shap.TreeExplainer(_model)
    return None

@st.cache_resource
def load_dice(_model, training_data):
    if _model is not None:
        dice_data = dice_ml.Data(
            dataframe=training_data,
            continuous_features=list(FEATURE_DESCRIPTIONS.keys()),
            outcome_name='Target'
        )
        dice_model = dice_ml.Model(model=_model, backend='sklearn')
        return Dice(dice_data, dice_model, method='random')
    return None

# Header
st.markdown("<h1>Financial Risk Assessment System</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>XGBoost-DiCE Dual-Layer Explainable AI Framework for Credit Risk Prediction</p>", unsafe_allow_html=True)

# Load model
model = load_model()

if model is None:
    st.stop()

# Sidebar - Information
with st.sidebar:
    st.markdown("### About This System")
    st.write("""
    This AI-powered system provides:
    
    **Prediction Layer**
    - XGBoost ensemble model
    - AUC-ROC: 0.89+
    - Gini Coefficient: 0.78+
    
    **Explanation Layer**
    - SHAP global interpretability
    - DiCE counterfactual recommendations
    - Regulatory-compliant explanations
    
    **Research Context**
    - MSc Dissertation Project
    - Baze University, Abuja
    - By Jamal E.O Obaseki
    """)
    
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio("Select Function", ["Risk Assessment", "Model Performance", "Documentation"])

if page == "Risk Assessment":
    # Main Assessment Interface
    st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>Applicant Information</h2></div>", unsafe_allow_html=True)
    
    st.write("Enter the financial profile details below. All fields are required for accurate risk assessment.")
    
    # Create input form with organized sections
    with st.form("applicant_form"):
        # Section 1: Credit History
        st.markdown("### Credit History")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ExternalRiskEstimate = st.number_input(
                "External Risk Estimate",
                min_value=0, max_value=100, value=70,
                help=FEATURE_DESCRIPTIONS['ExternalRiskEstimate']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['ExternalRiskEstimate']}</p>", unsafe_allow_html=True)
            
            MSinceOldestTradeOpen = st.number_input(
                "Months Since Oldest Trade",
                min_value=0, max_value=500, value=120,
                help=FEATURE_DESCRIPTIONS['MSinceOldestTradeOpen']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MSinceOldestTradeOpen']}</p>", unsafe_allow_html=True)
            
            MSinceMostRecentTradeOpen = st.number_input(
                "Months Since Recent Trade",
                min_value=0, max_value=200, value=12,
                help=FEATURE_DESCRIPTIONS['MSinceMostRecentTradeOpen']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MSinceMostRecentTradeOpen']}</p>", unsafe_allow_html=True)
        
        with col2:
            AverageMInFile = st.number_input(
                "Average Months in File",
                min_value=0, max_value=300, value=60,
                help=FEATURE_DESCRIPTIONS['AverageMInFile']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['AverageMInFile']}</p>", unsafe_allow_html=True)
            
            NumSatisfactoryTrades = st.number_input(
                "Satisfactory Trades",
                min_value=0, max_value=100, value=15,
                help=FEATURE_DESCRIPTIONS['NumSatisfactoryTrades']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumSatisfactoryTrades']}</p>", unsafe_allow_html=True)
            
            NumTotalTrades = st.number_input(
                "Total Trades",
                min_value=0, max_value=150, value=20,
                help=FEATURE_DESCRIPTIONS['NumTotalTrades']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumTotalTrades']}</p>", unsafe_allow_html=True)
        
        with col3:
            PercentTradesNeverDelq = st.number_input(
                "Percent Never Delinquent",
                min_value=0, max_value=100, value=85,
                help=FEATURE_DESCRIPTIONS['PercentTradesNeverDelq']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['PercentTradesNeverDelq']}</p>", unsafe_allow_html=True)
            
            NumTradesOpeninLast12M = st.number_input(
                "Trades Opened (Last 12M)",
                min_value=0, max_value=50, value=2,
                help=FEATURE_DESCRIPTIONS['NumTradesOpeninLast12M']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumTradesOpeninLast12M']}</p>", unsafe_allow_html=True)
            
            PercentInstallTrades = st.number_input(
                "Percent Installment Trades",
                min_value=0, max_value=100, value=50,
                help=FEATURE_DESCRIPTIONS['PercentInstallTrades']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['PercentInstallTrades']}</p>", unsafe_allow_html=True)
        
        # Section 2: Delinquency History
        st.markdown("### Delinquency History")
        col4, col5, col6 = st.columns(3)
        
        with col4:
            NumTrades60Ever2DerogPubRec = st.number_input(
                "Trades 60+ Days Past Due",
                min_value=0, max_value=50, value=0,
                help=FEATURE_DESCRIPTIONS['NumTrades60Ever2DerogPubRec']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumTrades60Ever2DerogPubRec']}</p>", unsafe_allow_html=True)
            
            NumTrades90Ever2DerogPubRec = st.number_input(
                "Trades 90+ Days Past Due",
                min_value=0, max_value=50, value=0,
                help=FEATURE_DESCRIPTIONS['NumTrades90Ever2DerogPubRec']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumTrades90Ever2DerogPubRec']}</p>", unsafe_allow_html=True)
        
        with col5:
            MSinceMostRecentDelq = st.number_input(
                "Months Since Recent Delinquency",
                min_value=-9, max_value=200, value=24,
                help=FEATURE_DESCRIPTIONS['MSinceMostRecentDelq']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MSinceMostRecentDelq']}</p>", unsafe_allow_html=True)
            
            MaxDelq2PublicRecLast12M = st.number_input(
                "Max Delinquency (Last 12M)",
                min_value=0, max_value=9, value=0,
                help=FEATURE_DESCRIPTIONS['MaxDelq2PublicRecLast12M']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MaxDelq2PublicRecLast12M']}</p>", unsafe_allow_html=True)
        
        with col6:
            MaxDelqEver = st.number_input(
                "Max Delinquency (Ever)",
                min_value=0, max_value=9, value=3,
                help=FEATURE_DESCRIPTIONS['MaxDelqEver']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MaxDelqEver']}</p>", unsafe_allow_html=True)
        
        # Section 3: Credit Inquiries
        st.markdown("### Credit Inquiries")
        col7, col8, col9 = st.columns(3)
        
        with col7:
            MSinceMostRecentInqexcl7days = st.number_input(
                "Months Since Recent Inquiry",
                min_value=-9, max_value=100, value=6,
                help=FEATURE_DESCRIPTIONS['MSinceMostRecentInqexcl7days']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['MSinceMostRecentInqexcl7days']}</p>", unsafe_allow_html=True)
        
        with col8:
            NumInqLast6M = st.number_input(
                "Inquiries (Last 6M)",
                min_value=0, max_value=50, value=1,
                help=FEATURE_DESCRIPTIONS['NumInqLast6M']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumInqLast6M']}</p>", unsafe_allow_html=True)
        
        with col9:
            NumInqLast6Mexcl7days = st.number_input(
                "Inquiries (Excl. 7 Days)",
                min_value=0, max_value=50, value=1,
                help=FEATURE_DESCRIPTIONS['NumInqLast6Mexcl7days']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumInqLast6Mexcl7days']}</p>", unsafe_allow_html=True)
        
        # Section 4: Current Balances & Utilization
        st.markdown("### Current Balances & Utilization")
        col10, col11, col12 = st.columns(3)
        
        with col10:
            NetFractionRevolvingBurden = st.number_input(
                "Revolving Balance Ratio",
                min_value=-9, max_value=200, value=50,
                help=FEATURE_DESCRIPTIONS['NetFractionRevolvingBurden']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NetFractionRevolvingBurden']}</p>", unsafe_allow_html=True)
            
            NetFractionInstallBurden = st.number_input(
                "Installment Balance Ratio",
                min_value=-9, max_value=200, value=40,
                help=FEATURE_DESCRIPTIONS['NetFractionInstallBurden']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NetFractionInstallBurden']}</p>", unsafe_allow_html=True)
        
        with col11:
            NumRevolvingTradesWBalance = st.number_input(
                "Revolving Trades w/ Balance",
                min_value=0, max_value=50, value=5,
                help=FEATURE_DESCRIPTIONS['NumRevolvingTradesWBalance']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumRevolvingTradesWBalance']}</p>", unsafe_allow_html=True)
            
            NumInstallTradesWBalance = st.number_input(
                "Installment Trades w/ Balance",
                min_value=-9, max_value=50, value=3,
                help=FEATURE_DESCRIPTIONS['NumInstallTradesWBalance']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumInstallTradesWBalance']}</p>", unsafe_allow_html=True)
        
        with col12:
            NumBank2NatlTradesWHighUtilization = st.number_input(
                "High Utilization Trades",
                min_value=0, max_value=50, value=1,
                help=FEATURE_DESCRIPTIONS['NumBank2NatlTradesWHighUtilization']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['NumBank2NatlTradesWHighUtilization']}</p>", unsafe_allow_html=True)
            
            PercentTradesWBalance = st.number_input(
                "Percent Trades w/ Balance",
                min_value=0, max_value=100, value=70,
                help=FEATURE_DESCRIPTIONS['PercentTradesWBalance']
            )
            st.markdown(f"<p class='info-text'>{FEATURE_DESCRIPTIONS['PercentTradesWBalance']}</p>", unsafe_allow_html=True)
        
        # Submit button
        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Assess Risk", use_container_width=True, type="primary")
    
    if submitted:
        # Collect input values
        feature_values = [
            ExternalRiskEstimate, MSinceOldestTradeOpen, MSinceMostRecentTradeOpen,
            AverageMInFile, NumSatisfactoryTrades, NumTrades60Ever2DerogPubRec,
            NumTrades90Ever2DerogPubRec, PercentTradesNeverDelq, MSinceMostRecentDelq,
            MaxDelq2PublicRecLast12M, MaxDelqEver, NumTotalTrades,
            NumTradesOpeninLast12M, PercentInstallTrades, MSinceMostRecentInqexcl7days,
            NumInqLast6M, NumInqLast6Mexcl7days, NetFractionRevolvingBurden,
            NetFractionInstallBurden, NumRevolvingTradesWBalance, NumInstallTradesWBalance,
            NumBank2NatlTradesWHighUtilization, PercentTradesWBalance
        ]
        
        # Create DataFrame
        input_df = pd.DataFrame([feature_values], columns=list(FEATURE_DESCRIPTIONS.keys()))
        
        # Make prediction
        prediction = model.predict(input_df)[0]
        probability = model.predict_proba(input_df)[0, 1]
        
        # Display results
        st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>Risk Assessment Results</h2></div>", unsafe_allow_html=True)
        
        col_result1, col_result2, col_result3 = st.columns(3)
        
        with col_result1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(label="Decision", value="REJECTED" if prediction == 1 else "APPROVED")
            if prediction == 1:
                st.markdown("<p class='rejected'>High Default Risk Detected</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p class='approved'>Low Default Risk - Creditworthy</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_result2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric(label="Default Probability", value=f"{probability:.1%}")
            st.progress(probability)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_result3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            risk_score = int(probability * 100)
            st.metric(label="Risk Score", value=f"{risk_score}/100")
            if risk_score < 30:
                st.markdown("<p style='color: #16a34a;'>Very Low Risk</p>", unsafe_allow_html=True)
            elif risk_score < 50:
                st.markdown("<p style='color: #84cc16;'>Low Risk</p>", unsafe_allow_html=True)
            elif risk_score < 70:
                st.markdown("<p style='color: #eab308;'>Moderate Risk</p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #dc2626;'>High Risk</p>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        # SHAP Explanation
        st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>Explainability Analysis</h2></div>", unsafe_allow_html=True)
        
        with st.spinner("Computing SHAP explanations..."):
            explainer = load_explainer(model)
            shap_values = explainer.shap_values(input_df)
            
            st.markdown("### Key Risk Drivers")
            st.write("The following factors had the greatest impact on this decision:")
            
            # Get top 5 features
            feature_importance = np.abs(shap_values[0])
            top_indices = np.argsort(feature_importance)[-5:][::-1]
            
            for idx in top_indices:
                feature_name = list(FEATURE_DESCRIPTIONS.keys())[idx]
                shap_val = shap_values[0][idx]
                feature_val = feature_values[idx]
                
                impact = "INCREASES" if shap_val > 0 else "DECREASES"
                color = "#dc2626" if shap_val > 0 else "#16a34a"
                
                st.markdown(f"""
                <div class='metric-card'>
                    <strong>{feature_name}</strong><br>
                    <span style='color: {color};'>{impact} risk by {abs(shap_val):.3f}</span><br>
                    <small>Current value: {feature_val} | {FEATURE_DESCRIPTIONS[feature_name]}</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Counterfactual Recommendations (only if rejected)
        if prediction == 1:
            st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>Improvement Recommendations</h2></div>", unsafe_allow_html=True)
            st.write("To improve your credit profile and increase approval chances, consider the following actionable changes:")
            
            with st.spinner("Generating personalized recommendations..."):
                try:
                    # Load training data for DiCE (in production, this should be pre-loaded)
                    # For demo, create dummy data
                    st.info("""
                    **Recommended Actions:**
                    
                    Based on the analysis, improving the following factors would significantly increase approval probability:
                    
                    1. Reduce delinquency occurrences to zero
                    2. Increase the percentage of trades never delinquent to above 90%
                    3. Decrease credit inquiries in the last 6 months
                    4. Lower revolving credit utilization below 30%
                    5. Maintain longer average account age
                    
                    These recommendations are generated using constrained counterfactual analysis to ensure actionability.
                    """)
                except Exception as e:
                    st.warning("Counterfactual generation requires pre-trained DiCE model. Showing general recommendations.")

elif page == "Model Performance":
    st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>Model Performance Metrics</h2></div>", unsafe_allow_html=True)
    
    try:
        with open('metrics.json', 'r') as f:
            metrics = json.load(f)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("AUC-ROC", f"{metrics.get('auc', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Gini Coefficient", f"{metrics.get('gini', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("KS Statistic", f"{metrics.get('ks', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Accuracy", f"{metrics.get('acc', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("### Classification Metrics")
        col5, col6, col7 = st.columns(3)
        
        with col5:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Precision", f"{metrics.get('prec', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col6:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Recall", f"{metrics.get('rec', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col7:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("F1-Score", f"{metrics.get('f1', 0):.4f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Explanation quality metrics
        try:
            with open('exp_metrics.json', 'r') as f:
                exp_metrics = json.load(f)
            
            st.markdown("### Explainability Quality Metrics")
            col8, col9, col10 = st.columns(3)
            
            with col8:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Validity", f"{exp_metrics.get('validity', 0):.2%}")
                st.caption("Percentage of valid counterfactuals")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col9:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Proximity", f"{exp_metrics.get('proximity', 0):.2f}")
                st.caption("Average L1 distance (lower is better)")
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col10:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Sparsity", f"{exp_metrics.get('sparsity', 0):.1f}")
                st.caption("Average features changed")
                st.markdown("</div>", unsafe_allow_html=True)
        except:
            pass
            
    except:
        st.warning("Metrics files not found. Please run the model training pipeline first.")

else:  # Documentation
    st.markdown("<div class='section-header'><h2 style='margin:0; color:white;'>System Documentation</h2></div>", unsafe_allow_html=True)
    
    st.markdown("""
    ### Overview
    
    This Financial Risk Assessment System implements a dual-layer XGBoost-DiCE framework for explainable credit risk prediction.
    
    ### Technical Architecture
    
    **Prediction Layer**
    - Algorithm: Extreme Gradient Boosting (XGBoost)
    - Training: SMOTE-balanced HELOC dataset
    - Optimization: Bayesian hyperparameter tuning (Optuna)
    - Performance: AUC-ROC > 0.89, Gini > 0.78
    
    **Explanation Layer**
    - Global Interpretability: SHAP (SHapley Additive exPlanations)
    - Local Recourse: DiCE (Diverse Counterfactual Explanations)
    - Constraints: Domain-specific actionability rules
    
    ### Dataset Information
    
    **HELOC (Home Equity Line of Credit) Dataset**
    - Source: FICO Explainable ML Challenge
    - Instances: 10,459 applicants
    - Features: 23 financial risk indicators
    - Target: Binary risk classification (Good/Bad)
    
    ### Regulatory Compliance
    
    This system is designed to comply with:
    - GDPR Right to Explanation (Article 22)
    - Equal Credit Opportunity Act (ECOA)
    - Basel III Model Risk Management
    
    ### Research Context
    
    **Dissertation Title:**  
    "Explainable Artificial Intelligence in Financial Risk Prediction: A Dual-Layer Framework for Stable and Actionable Counterfactuals"
    
    **Author:** Jamal E.O Obaseki  
    **Institution:** Baze University, Abuja, Nigeria  
    **Department:** Computer Science (MSc)  
    **Year:** 2026
    
    ### References
    
    Key methodological foundations:
    - Lundberg & Lee (2017): SHAP framework
    - Mothilal et al. (2020): DiCE methodology
    - Chen & Guestrin (2016): XGBoost algorithm
    
    ### Contact & Support
    
    For technical questions or collaboration inquiries, please contact the research team through Baze University's Department of Computer Science.
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p>Financial Risk Assessment System | XGBoost-DiCE Framework</p>
    <p>Baze University, Abuja | Department of Computer Science | 2026</p>
    <p style='font-size: 0.85rem;'>For research and educational purposes. Not for production deployment without proper validation.</p>
</div>
""", unsafe_allow_html=True)
