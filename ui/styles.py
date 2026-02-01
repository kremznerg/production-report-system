import streamlit as st

def apply_custom_css():
    """Alkalmazza a dashboard egyedi CSS stílusait."""
    st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        scroll-behavior: smooth;
    }

    .main {
        background-color: #f8f9fa;
    }

    /* REDUCE TOP PADDING */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
    }
    
    /* GLASSMORPHISM CARD */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
        border: 1px solid rgba(13, 110, 253, 0.2);
    }

    /* SECTION CARDS */
    .st-card {
        background: #ffffff;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #f1f3f5;
        margin-bottom: 20px;
    }

    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #6c757d !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem !important;
    }

    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #212529 !important;
        font-size: 1.8rem !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }

    /* COMPACT SIDEBAR */
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }

    section[data-testid="stSidebar"] h1 {
        margin-top: 10px !important;
        margin-bottom: 10px !important;
        font-size: 1.8rem !important;
    }

    /* SIDEBAR INPUTS HIGHLIGHT */
    section[data-testid="stSidebar"] [data-testid="stSelectbox"],
    section[data-testid="stSidebar"] [data-testid="stDateInput"] {
        background-color: #f1f3f5 !important;
        padding: 12px !important;
        border-radius: 12px !important;
        border: 1px solid #dee2e6 !important;
        margin-bottom: 10px !important;
    }

    section[data-testid="stSidebar"] hr {
        margin-top: 10px !important;
        margin-bottom: 20px !important;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #495057;
        font-weight: 600;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
    }

    .stTabs [aria-selected="true"] {
        color: #0d6efd !important;
        border-bottom: 2px solid #0d6efd !important;
    }

    /* FLOATING BACK TO TOP BUTTON */
    .back-to-top {
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: #0d6efd;
        color: white !important;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        cursor: pointer;
        z-index: 9999;
        transition: all 0.3s ease;
        text-decoration: none !important;
        font-size: 24px;
        font-weight: bold;
    }

    .back-to-top:hover {
        transform: translateY(-5px);
        background: #0b5ed7;
        box-shadow: 0 6px 16px rgba(0,0,0,0.3);
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)
