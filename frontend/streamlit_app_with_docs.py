import streamlit as st
import requests
import re
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import docx
import PyPDF2
import io
import json
import streamlit.components.v1 as components
from fpdf import FPDF

# --- Configuration & State Management ---
st.set_page_config(
    page_title="PaperIQ",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'users' not in st.session_state:
    st.session_state['users'] = {'admin': 'admin'} # Default admin user
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'theme' not in st.session_state:
    st.session_state['theme'] = 'light'
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Prefer environment variable, fall back to st.secrets if present.
API_URL = os.environ.get("PAPERIQ_API_URL", "http://localhost:8000/analyze")

def toggle_theme():
    if st.session_state['theme'] == 'light':
        st.session_state['theme'] = 'dark'
    else:
        st.session_state['theme'] = 'light'

def inject_custom_css():
    theme = st.session_state['theme']
    
    if theme == 'dark':
        # Dark Mode Variables
        bg_color = "#121212"
        secondary_bg = "#1e1e1e"
        text_color = "#ffffff"
        card_bg = "#2d2d2d"
        border_color = "#404040"
    else:
        # Light Mode Variables
        bg_color = "#f0f2f6"
        secondary_bg = "#ffffff"
        text_color = "#1a1a1a"
        card_bg = "#ffffff"
        border_color = "#e0e0e0"

    st.markdown(f"""
    <style>
        /* Modern Font Import */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Global Theme Overrides */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {secondary_bg};
        }}
        
        /* Inputs */
        .stTextInput input, .stTextArea textarea {{
            background-color: {secondary_bg};
            color: {text_color};
            border: 1px solid {border_color};
        }}

        /* File Uploader Container */
        [data-testid="stFileUploader"] {{
            background-color: {secondary_bg};
            border-radius: 10px;
            padding: 1rem;
        }}
        [data-testid="stFileUploader"] section {{
            background-color: {secondary_bg};
        }}
        
        /* FINAL NUCLEAR OPTION FOR BUTTONS */
        /* Target every single button in the app that isn't primary */
        html body .stApp button:not([kind="primary"]) {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
        }}
        
        html body .stApp button:not([kind="primary"]) * {{
            color: {text_color} !important;
        }}
        
        /* Specific targeting for Streamlit buttons */
        html body .stApp [data-testid="stButton"] > button:not([kind="primary"]) {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
        }}

        /* Hover State */
        html body .stApp button:not([kind="primary"]):hover {{
            border-color: #4caf50 !important;
            color: #4caf50 !important;
        }}
        
        html body .stApp button:not([kind="primary"]):hover * {{
            color: #4caf50 !important;
        }}

        /* Primary Buttons & Download Button (Green) */
        button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        div[data-testid="stFormSubmitButton"] > button, 
        div.stDownloadButton > button {{
            background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%) !important;
            color: white !important;
            border: none !important;
        }}
        
        button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button:hover, 
        div.stDownloadButton > button:hover {{
            background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%) !important;
            color: white !important;
            box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3) !important;
        }}
        
        button[kind="primary"] p,
        button[data-testid="stBaseButton-primary"] p,
        div[data-testid="stFormSubmitButton"] > button p,
        div.stDownloadButton > button p {{
            color: white !important;
        }}
        
        /* Feature Cards & Glass Cards */
        .feature-card, .glass-card, .profile-stat-card {{
            background: {card_bg} !important;
            border: 1px solid {border_color} !important;
            color: {text_color} !important;
        }}
        .feature-card h3, .feature-card p, .stat-value, .stat-label {{
            color: {text_color} !important;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6, p, span, div {{
            color: {text_color} !important;
        }}
        
        /* Document Preview */
        .paper-preview {{
            background-color: {card_bg};
            color: {text_color} !important;
            border: 1px solid {border_color};
        }}
        
        /* Expander */
        .streamlit-expanderHeader, .streamlit-expanderContent {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {text_color} !important;
        }}
        
        /* Theme Toggle Button Position */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 5rem;
            z-index: 999999;
        }}
    </style>
    """, unsafe_allow_html=True)

# --- PDF Generation Helper ---
class PDF(FPDF):
    def header(self):
        # Logo / Brand
        self.set_font('Arial', 'B', 20)
        self.set_text_color(46, 125, 50) # PaperIQ Green
        self.cell(0, 10, 'PaperIQ Analysis Report', 0, 1, 'L')
        self.ln(5)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_pdf_report(data):
    pdf = PDF()
    pdf.add_page()
    
    # --- Executive Summary ---
    pdf.set_fill_color(240, 248, 240) # Light Green Background
    pdf.rect(10, 30, 190, 40, 'F')
    
    pdf.set_y(35)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Executive Summary", 0, 1, 'L')
    
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(95, 15, f"{data['composite']}/100", 0, 0, 'C')
    
    pdf.set_font("Arial", '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(110, 45)
    pdf.cell(0, 5, f"Language Quality: {data['language']}", 0, 1)
    pdf.set_x(110)
    pdf.cell(0, 5, f"Coherence: {data['coherence']}", 0, 1)
    pdf.set_x(110)
    pdf.cell(0, 5, f"Reasoning: {data['reasoning']}", 0, 1)
    
    pdf.ln(25)
    
    # --- Detailed Metrics ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Detailed Diagnostics", 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    diag = data['diagnostics']
    metrics = [
        ("Word Count", str(diag.get('word_count', 'N/A'))),
        ("Sentence Count", str(diag.get('sentence_count', 'N/A'))),
        ("Avg Sentence Length", f"{diag.get('avg_sentence_len', 0):.2f}"),
        ("Avg Word Length", f"{diag.get('avg_word_len', 0):.2f}"),
        ("Vocabulary Diversity", f"{diag.get('ttr', 0):.2f}"),
        ("Lexical Sophistication", f"{diag.get('lex_soph', 0):.2f}"),
        ("Coherence Score", f"{diag.get('coherence', 0):.2f}"),
        ("Reasoning Score", f"{diag.get('reasoning_proxy', 0):.2f}"),
        ("Sentiment Polarity", f"{diag.get('sentiment_polarity', 0):.2f}"),
        ("Subjectivity", f"{diag.get('sentiment_subjectivity', 0):.2f}")
    ]
    
    pdf.set_font("Arial", '', 10)
    col_width = 90
    row_height = 8
    
    for i, (name, value) in enumerate(metrics):
        if i % 2 == 0:
            pdf.set_fill_color(250, 250, 250)
            pdf.rect(10, pdf.get_y(), 190, row_height, 'F')
        
        pdf.cell(col_width, row_height, name, 0, 0)
        pdf.cell(col_width, row_height, value, 0, 1)
        
    pdf.ln(10)
    
    # --- Flagged Sentences ---
    if data.get('top_flagged_sentences'):
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Areas for Improvement", 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 10)
        for i, s in enumerate(data['top_flagged_sentences']):
            sentence_text = s if isinstance(s, str) else s.get('sentence', '')
            sentence_text = sentence_text.encode('latin-1', 'replace').decode('latin-1')
            
            pdf.set_fill_color(255, 243, 224) # Light Orange
            pdf.rect(10, pdf.get_y(), 190, 8, 'F')
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 8, f"Flagged Sentence #{i+1}", 0, 1)
            
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, sentence_text)
            pdf.ln(5)
            
    return pdf.output(dest='S').encode('latin-1')

# --- Configuration & State Management ---
st.set_page_config(
    page_title="PaperIQ",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'page' not in st.session_state:
    st.session_state['page'] = 'landing'
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'users' not in st.session_state:
    st.session_state['users'] = {'admin': 'admin'} # Default admin user
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None

# Prefer environment variable, fall back to st.secrets if present.
API_URL = os.environ.get("PAPERIQ_API_URL", "http://localhost:8000/analyze")
try:
    API_URL = st.secrets.get("API_URL", API_URL)
except Exception:
    pass

# --- Custom CSS ---
def inject_custom_css():
    theme = st.session_state['theme']
    
    if theme == 'dark':
        # Dark Mode Variables
        bg_color = "#121212"
        secondary_bg = "#1e1e1e"
        text_color = "#ffffff"
        card_bg = "#2d2d2d"
        border_color = "#404040"
    else:
        # Light Mode Variables
        bg_color = "#f0f2f6"
        secondary_bg = "#ffffff"
        text_color = "#1a1a1a"
        card_bg = "#ffffff"
        border_color = "#e0e0e0"

    st.markdown(f"""
    <style>
        /* Modern Font Import */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}
        
        /* Global Theme Overrides */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {secondary_bg};
        }}
        
        /* Inputs */
        .stTextInput input, .stTextArea textarea {{
            background-color: {secondary_bg};
            color: {text_color};
            border: 1px solid {border_color};
        }}
        
        /* Feature Cards & Glass Cards */
        .feature-card, .glass-card, .profile-stat-card {{
            background: {card_bg} !important;
            border: 1px solid {border_color} !important;
            color: {text_color} !important;
        }}
        .feature-card h3, .feature-card p, .stat-value, .stat-label {{
            color: {text_color} !important;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6, p, span, div {{
            color: {text_color} !important;
        }}
        
        /* Document Preview */
        .paper-preview {{
            background-color: {card_bg};
            color: {text_color} !important;
            border: 1px solid {border_color};
            white-space: pre-wrap;
            padding: 1rem;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9rem;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        /* Expander */
        /* Expander */
        [data-testid="stExpander"] {{
            background-color: {card_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 8px !important;
        }}
        
        [data-testid="stExpander"] details {{
            background-color: {card_bg} !important;
            border-radius: 8px !important;
        }}

        [data-testid="stExpander"] summary {{
            color: {text_color} !important;
            font-weight: 600 !important;
        }}

        [data-testid="stExpander"] summary:hover {{
            color: #2e7d32 !important;
        }}

        [data-testid="stExpander"] div[role="button"] p {{
            color: {text_color} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {text_color} !important;
        }}
        
        /* Theme Toggle Button Position */
        .theme-toggle {{
            position: fixed;
            top: 1rem;
            right: 5rem;
            z-index: 999999;
        }}

        /* --- TABS STYLING (Pill Design) --- */
        [data-testid="stTabs"] {{
            background-color: transparent;
            gap: 10px;
        }}

        [data-testid="stTabs"] button {{
            border-radius: 20px !important;
            padding: 0.5rem 1.5rem !important;
            font-weight: 600 !important;
            border: none !important;
            background-color: transparent !important;
            color: {text_color} !important;
            transition: all 0.3s ease !important;
        }}

        /* Active Tab */
        [data-testid="stTabs"] button[aria-selected="true"] {{
            background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%) !important;
            color: white !important;
            box-shadow: 0 4px 12px rgba(46, 125, 50, 0.3) !important;
        }}

        /* Hover State */
        [data-testid="stTabs"] button:hover {{
            color: #43a047 !important;
            background-color: rgba(67, 160, 71, 0.1) !important;
        }}

        /* --- LANDING PAGE STYLES (Card Design) --- */
        
        /* Hero Card */
        .hero-card {{
            background-color: {card_bg};
            padding: 4rem 2rem;
            border-radius: 24px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            text-align: center;
            margin-bottom: 2rem;
            border: 1px solid {border_color};
        }}
        
        .hero-title {{
            font-size: 4rem;
            font-weight: 800;
            color: #2e7d32; /* PaperIQ Green */
            margin-bottom: 1rem;
            letter-spacing: -1px;
        }}
        
        .hero-subtitle {{
            font-size: 1.2rem;
            color: {text_color};
            opacity: 0.7;
            margin-bottom: 0;
        }}
        
        /* Feature Cards */
        .feature-card {{
            background-color: {card_bg};
            padding: 2.5rem 1.5rem;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            text-align: center;
            height: 100%;
            border: 1px solid {border_color};
            transition: transform 0.2s ease;
        }}
        
        .feature-card:hover {{
            transform: translateY(-5px);
        }}
        
        .feature-icon {{
            font-size: 3rem;
            margin-bottom: 1.5rem;
        }}
        
        .feature-card h3 {{
            font-size: 1.5rem;
            font-weight: 700;
            color: #2e7d32;
            margin-bottom: 1rem;
        }}
        
        .feature-card p {{
            font-size: 1rem;
            color: {text_color};
            opacity: 0.8;
            line-height: 1.6;
        }}
        
        /* File Uploader Container */
        [data-testid="stFileUploader"] {{
            background-color: {secondary_bg};
            border-radius: 10px;
            padding: 1rem;
        }}
        [data-testid="stFileUploader"] section {{
            background-color: {secondary_bg};
        }}
        
        /* FINAL NUCLEAR OPTION FOR BUTTONS */
        /* Target every single button in the app that isn't primary */
        html body .stApp button:not([kind="primary"]) {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
            border: 1px solid {border_color} !important;
        }}
        
        html body .stApp button:not([kind="primary"]) * {{
            color: {text_color} !important;
        }}
        
        /* Specific targeting for Streamlit buttons */
        html body .stApp [data-testid="stButton"] > button:not([kind="primary"]) {{
            background-color: {card_bg} !important;
            color: {text_color} !important;
        }}

        /* Hover State */
        html body .stApp button:not([kind="primary"]):hover {{
            border-color: #4caf50 !important;
            color: #4caf50 !important;
        }}
        
        html body .stApp button:not([kind="primary"]):hover * {{
            color: #4caf50 !important;
        }}

        /* Primary Buttons & Download Button (Green) */
        button[kind="primary"],
        button[data-testid="stBaseButton-primary"],
        div[data-testid="stFormSubmitButton"] > button, 
        div.stDownloadButton > button {{
            background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%) !important;
            color: white !important;
            border: none !important;
        }}
        
        button[kind="primary"]:hover,
        button[data-testid="stBaseButton-primary"]:hover,
        div[data-testid="stFormSubmitButton"] > button:hover, 
        div.stDownloadButton > button:hover {{
            background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%) !important;
            color: white !important;
            box-shadow: 0 8px 20px rgba(46, 125, 50, 0.3) !important;
        }}
        
        button[kind="primary"] p,
        button[data-testid="stBaseButton-primary"] p,
        div[data-testid="stFormSubmitButton"] > button p,
        div.stDownloadButton > button p {{
            color: white !important;
        }}

    </style>
    """, unsafe_allow_html=True)

inject_custom_css()

def show_landing_page():
    # Theme Toggle
    col_t1, col_t2 = st.columns([10, 1])
    with col_t2:
        btn_label = "🌙" if st.session_state['theme'] == 'light' else "☀️"
        if st.button(btn_label, key="theme_toggle_landing"):
            toggle_theme()
            st.rerun()

    # Hero Card
    st.markdown("""
        <div class="hero-card">
            <h1 class="hero-title">PaperIQ</h1>
            <p class="hero-subtitle">Elevate Your Academic Writing with AI-Powered Insights</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3>Precision Analysis</h3>
            <p>Get deep insights into vocabulary, coherence, and reasoning strength.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3>Visual Metrics</h3>
            <p>Understand your writing style through interactive charts and scores.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🚀</div>
            <h3>Instant Feedback</h3>
            <p>Improve your essays and papers in seconds with actionable advice.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    st.write("")
    
    # Call to Action
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("Get Started Now", use_container_width=True, type="primary"):
            st.session_state['page'] = 'login'
            st.rerun()


def show_signup_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-bottom: 2rem;'><h1>Create Account</h1></div>", unsafe_allow_html=True)
        
        with st.form("signup_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up", use_container_width=True, type="primary")
            
            if submitted:
                if not new_username or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                elif new_username in st.session_state['users']:
                    st.error("Username already exists.")
                else:
                    st.session_state['users'][new_username] = new_password
                    st.success("Account created! Please log in.")
                    st.session_state['page'] = 'login'
                    st.rerun()
        if st.button("← Back to Login"):
            st.session_state['page'] = 'login'
            st.rerun()

def show_login_page():
    # Auto-redirect if already authenticated
    if st.session_state.get('authenticated', False):
        st.session_state['page'] = 'app'
        st.rerun()

    # Theme Toggle
    col_t1, col_t2 = st.columns([10, 1])
    with col_t2:
        btn_label = "🌙" if st.session_state['theme'] == 'light' else "☀️"
        if st.button(btn_label, key="theme_toggle_login"):
            toggle_theme()
            st.rerun()

    st.markdown("""
        <style>
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        .login-header h1 {
            color: #2e7d32 !important;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .login-header p {
            color: #666;
            font-size: 1.1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
            <div class="login-header">
                <h1>PaperIQ</h1>
                <p>Sign in to your account</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")
            
            if submitted:
                if username in st.session_state['users'] and st.session_state['users'][username] == password:
                    st.session_state['authenticated'] = True
                    st.session_state['current_user'] = username
                    st.session_state['page'] = 'app'
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        
        st.markdown("""
            <div style="text-align: center; margin: 1rem 0; color: #666;">
                — OR —
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("Continue with Google", use_container_width=True):
            try:
                import google_auth
                auth_url = google_auth.get_auth_url()
                if auth_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                else:
                    st.error("Missing `client_secrets.json`. Please add it to the project root.")
            except ImportError:
                 st.error("Google Auth libraries not installed. Please run `pip install google-auth-oauthlib`.")
            except Exception as e:
                st.error(f"Error initializing Google Login: {str(e)}")
        
        # Handle OAuth Callback - REMOVED (Handled Globally)
        # Logic moved to main execution flow to prevent redirect loops

        
        st.markdown("<div style='text-align: center; margin-top: 1.5rem;'>", unsafe_allow_html=True)
        st.markdown("New to PaperIQ?")
        if st.button("Create an Account", type="secondary", use_container_width=True):
            st.session_state['page'] = 'signup'
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("← Back to Home", use_container_width=True):
            st.session_state['page'] = 'landing'
            st.rerun()

def show_profile_page():
    st.markdown("""
        <style>
        .profile-stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            text-align: center;
            border: 1px solid #eee;
            transition: transform 0.2s;
        }
        .profile-stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #2e7d32;
        }
        .stat-label {
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .avatar-circle {
            width: 80px;
            height: 80px;
            background-color: #e8f5e9;
            color: #2e7d32;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.5rem;
            font-weight: bold;
            margin: 0 auto;
            border: 2px solid #2e7d32;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header Section
    col1, col2 = st.columns([1, 4])
    with col1:
        username = st.session_state.get('current_user', 'User')
        initial = username[0].upper() if username else "U"
        st.markdown(f'<div class="avatar-circle">{initial}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"# Hello, {username}!")
        st.markdown("### Standard Plan Member")
        st.caption("Member since November 2025 • Next billing date: Dec 29, 2025")

    st.markdown("---")
    
    # Stats Grid
    st.subheader("📊 Your Performance")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("""
            <div class="profile-stat-card">
                <div class="stat-value">12</div>
                <div class="stat-label">Papers Analyzed</div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
            <div class="profile-stat-card">
                <div class="stat-value">78.5</div>
                <div class="stat-label">Avg. Score</div>
            </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
            <div class="profile-stat-card">
                <div class="stat-value">15k</div>
                <div class="stat-label">Words Checked</div>
            </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
            <div class="profile-stat-card">
                <div class="stat-value">4.8</div>
                <div class="stat-label">Avg. Coherence</div>
            </div>
        """, unsafe_allow_html=True)
        
    st.write("")
    st.write("")
    
    # Recent Activity
    st.subheader("🕒 Recent Activity")
    
    activities = st.session_state.get('history', [])
    
    if not activities:
        st.info("No recent activity found.")
    else:
        for i, act in enumerate(activities):
            with st.expander(f"{act['date']} - {act['action']}"):
                st.write(f"**Score:** {act['score']}/100")
                if st.button("View Report", key=f"btn_history_{i}"):
                    st.session_state['analysis_results'] = act['data']
                    st.session_state['page'] = 'results'
                    st.rerun()
    
    st.markdown("---")
    if st.button("← Back to Dashboard", use_container_width=True):
        st.session_state['page'] = 'app'
        st.rerun()

def clean_text(text):
    """
    Cleans text by replacing common PDF extraction artifacts/ligatures.
    Uses regex to handle potential whitespace before the ligature.
    """
    # Regex replacements for ligatures (consuming preceding whitespace)
    regex_replacements = [
        (r'\s*Ɵ', 'ti'),
        (r'\s*Ʃ', 'tt'),
        (r'\s*Ō', 'ft'),
        (r'\s*ﬂ', 'fl'),
        (r'\s*ﬁ', 'fi'),
        (r'\s*ﬀ', 'ff'),
        (r'\s*ﬃ', 'ffi'),
        (r'\s*ﬄ', 'ffl'),
    ]
    
    for pattern, repl in regex_replacements:
        text = re.sub(pattern, repl, text)

    # Simple string replacements for others
    simple_replacements = {
        '’': "'",
        '“': '"',
        '”': '"',
        '–': '-',
        '—': '-'
    }
    for k, v in simple_replacements.items():
        text = text.replace(k, v)
        
    # Fix specific common broken words if they persist (fallback)
    # This handles cases where the ligature might have been already converted but with a space
    text = re.sub(r'wri\s+ting', 'writing', text, flags=re.IGNORECASE)
    text = re.sub(r'interac\s+tive', 'interactive', text, flags=re.IGNORECASE)
    text = re.sub(r'descrip\s+tive', 'descriptive', text, flags=re.IGNORECASE)
    text = re.sub(r'dra\s+fts', 'drafts', text, flags=re.IGNORECASE)
    
    return text

def show_main_app():
    # Header with Logout & Theme Toggle
    col_brand, col_spacer, col_user, col_theme = st.columns([2, 4, 3, 1])
    with col_brand:
        st.markdown("### 🧠 PaperIQ")
    with col_user:
        c_prof, c_out = st.columns([1, 1])
        with c_prof:
            if st.button("👤 Profile"):
                st.session_state['page'] = 'profile'
                st.rerun()
        with c_out:
            if st.button("Log Out"):
                st.session_state['authenticated'] = False
                st.session_state['current_user'] = None
                st.session_state['page'] = 'landing'
                st.rerun()
    with col_theme:
        btn_label = "🌙" if st.session_state['theme'] == 'light' else "☀️"
        if st.button(btn_label, key="theme_toggle_app"):
            toggle_theme()
            st.rerun()
            
    st.markdown("---")

    # --- Sidebar / UX helpers ---
    with st.sidebar:
        st.header("Quick Actions")
        st.markdown("Paste text or upload a PDF/DOCX, then click **Analyze**.")
        st.markdown("---")
        st.markdown("**API Status**")
        if st.button("Check API Health"):
            try:
                health_url = API_URL.rstrip('/') + '/health'
                r = requests.get(health_url, timeout=3)
                if r.status_code == 200 and r.json().get('status') == 'ok':
                    st.success("System Operational")
                else:
                    st.error(f"Status: {r.status_code}")
            except Exception as e:
                st.error("System Offline")
        st.markdown("---")
        st.markdown("**Tips**")
        st.info("Paste a paper excerpt for quick checks, or upload full PDF/DOCX for thorough analysis.")

    # Create main navigation
    tab_main, tab_docs = st.tabs(["📝 Analysis Tool", "📚 Documentation"])

    with tab_main:
        st.markdown("### Upload or Paste your document")
        st.markdown("Supported formats: PDF (.pdf), Word (.docx) or paste text below")

        text_area_col, upload_col = st.columns([3,1])
        with text_area_col:
            pasted_text = st.text_area("Paste paper excerpt", height=200, placeholder="Enter your text here...")
        with upload_col:
            uploaded_file = st.file_uploader("Upload file", type=['pdf', 'docx'])

        text = pasted_text or ""
        
        if uploaded_file is not None:
            try:
                if uploaded_file.type == "application/pdf":
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(uploaded_file)
                    text = ""
                    for page in pdf_reader.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text += clean_text(extracted) + "\n"
                
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    doc = docx.Document(uploaded_file)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
                text = ""
            
            st.markdown("### Document Preview")
            with st.expander("Show document content", expanded=True):
                st.markdown(f'<div class="paper-preview">{text[:2000] + ("..." if len(text) > 2000 else "")}</div>', unsafe_allow_html=True)

        if st.button("Analyze Document", type="primary", use_container_width=True):
            if not text.strip():
                st.warning("Please enter some text or upload a file.")
            else:
                with st.spinner("Analyzing..."):
                    try:
                        payload = {"text": text}
                        response = requests.post(API_URL, json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state['analysis_results'] = data
                            
                            # Add to history
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%b %d, %I:%M %p")
                            # Create a short action description
                            action_desc = f"Analyzed text ({len(text)} chars)"
                            
                            st.session_state['history'].insert(0, {
                                "date": timestamp,
                                "action": action_desc,
                                "score": int(data['composite']),
                                "data": data
                            })
                            
                            st.session_state['page'] = 'results'
                            st.rerun()
                        else:
                            st.error(f"Error {response.status_code}: {response.text}")
                    except Exception as e:
                        st.error(f"Failed to call API: {str(e)}")
    with tab_docs:
        st.markdown("""
        # 📚 PaperIQ Documentation
        
        ## Overview
        PaperIQ is an AI-powered tool designed to analyze and provide insights into academic writing. 
        It evaluates text across multiple dimensions and provides detailed feedback to help improve 
        - **Average Word Length**: Characters per word
        - **Vocabulary Diversity (TTR)**: Ratio of unique words to total words
        - **Lexical Sophistication**: Measure of advanced vocabulary usage
        
        #### Text Structure
        - **Coherence Score**: Measures how well ideas flow and connect
        - **Reasoning Assessment**: Evaluates logical structure and argumentation
        
        ### 3. Visualizations
        - **Radar Chart**: Shows balance between main components
        - **Bar Charts**: Detailed breakdown of language metrics
        - **Comparative Analysis**: Contextual feedback on writing style
        
        ## 💡 How to Use
        
        1. **Input Your Text**
           - Paste your text in the main text area
           - Or upload a PDF/DOCX file
           - Minimum 20 characters required
        
        2. **Analyze**
           - Click the "Analyze" button
           - Wait for the analysis to complete
        
        3. **Review Results**
           - Check the main scores
           - Explore detailed metrics
           - Review visualizations
           - Read contextual feedback
        
        ## 📊 Understanding Scores
        
        ### Composite Score (0-100)
        - **90-100**: Exceptional
        - **80-89**: Strong
        - **70-79**: Good
        - **60-69**: Adequate
        - **Below 60**: Needs improvement
        
        ### Component Scores
        Each component (Language, Coherence, Reasoning) is scored from 0-100:
        - **Language**: Evaluates writing mechanics and style
        - **Coherence**: Measures text flow and organization
        - **Reasoning**: Assesses logical structure
        
        ## 🔍 Advanced Metrics Explained
        
        ### Vocabulary Diversity (TTR)
        - **>0.7**: Excellent diversity
        - **0.5-0.7**: Good range
        - **<0.5**: Limited variety
        
        ### Sentence Length
        - **15-25 words**: Ideal for academic writing
        - **<15 words**: May be too brief
        - **>25 words**: Consider breaking down
        
        ## 🚀 Best Practices
        
        1. **For Academic Papers**
           - Aim for sentence length of 15-25 words
           - Maintain high vocabulary diversity
           - Ensure strong coherence between paragraphs
        
        2. **For Technical Writing**
           - Use precise terminology
           - Maintain clear logical structure
           - Balance complexity with clarity
        
        3. **For General Writing**
           - Focus on flow and readability
           - Vary sentence structure
           - Use appropriate vocabulary
        """)

def show_results_page():
    # Header with Back Button
    c_back, c_brand = st.columns([1, 5])
    with c_back:
        if st.button("← Analyze Another"):
            st.session_state['page'] = 'app'
            st.rerun()
    with c_brand:
        st.markdown("### 📊 Analysis Results")
    
    st.markdown("---")

    if 'analysis_results' not in st.session_state:
        st.error("No results found. Please go back and analyze a document.")
        return

    data = st.session_state['analysis_results']

    # --- Top Level Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Composite Score", f"{data['composite']}/100")
    with col2:
        st.metric("Language", f"{data['language']}/100")
    with col3:
        st.metric("Coherence", f"{data['coherence']}/100")
    with col4:
        st.metric("Reasoning", f"{data['reasoning']}/100")

    st.write("")
    
    # Download Buttons
    d_col1, d_col2, d_col3 = st.columns([1, 2, 1])
    with d_col2:
        try:
            pdf_bytes = create_pdf_report(data)
            st.download_button("Download PDF Report", data=pdf_bytes, file_name="papereval.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            st.error(f"PDF Generation Error: {str(e)}")

    # --- Charts & Detailed Analysis ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Visualizations", "🚩 Issues", "💡 Suggestions", "📋 Detailed Metrics", "💭 Sentiment"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            # Radar Chart
            categories = ['Language', 'Coherence', 'Reasoning', 'Lexical Sophistication', 'Text Standard']
            values = [
                data['language'], 
                data['coherence'], 
                data['reasoning'], 
                min(data['diagnostics']['lex_soph'] * 100, 100),
                min(data['diagnostics']['ttr'] * 100, 100)
            ]
            
            fig = go.Figure(data=go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='PaperIQ Score'
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                title="Metric Radar"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            # Bar Chart for Diagnostics
            diag = data['diagnostics']
            metrics_df = pd.DataFrame({
                'Metric': ['Avg Sentence Len', 'Avg Word Len'],
                'Value': [diag['avg_sentence_len'], diag['avg_word_len']]
            })
            fig_bar = px.bar(metrics_df, x='Metric', y='Value', title="Text Statistics", color='Metric')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Flagged Sentences")
        if data.get('top_flagged_sentences'):
            for i, s in enumerate(data['top_flagged_sentences']):
                # Handle if s is just a string
                if isinstance(s, str):
                    with st.expander(f"Flagged Sentence #{i+1}", expanded=True):
                        st.write(f"**Sentence:** {s}")
                        st.warning("This sentence was flagged for potential improvement.")
                else:
                    # Fallback if it is a dict
                    with st.expander(f"Flagged: \"{s.get('sentence', '')[:50]}...\"", expanded=True):
                        st.write(f"**Full Sentence:** {s.get('sentence', '')}")
                        st.write(f"**Issue:** {s.get('reason', 'N/A')}")
                        st.info(f"**Suggestion:** {s.get('suggestion', 'N/A')}")
        else:
            st.success("No critical issues found!")

    with tab3:
        st.subheader("General Improvements")
        if data['composite'] < 70:
            st.warning("Your paper needs significant revision. Focus on clarity and structure.")
        elif data['composite'] < 90:
            st.info("Good work! Focus on vocabulary variety and stronger transitions to reach the next level.")
        else:
            st.success("Excellent work! Your paper is well-written and structured.")
            
    with tab4:
        st.subheader("Detailed Metrics")
        
        metric_names = {
            'word_count': 'Total Word Count',
            'sentence_count': 'Number of Sentences',
            'avg_sentence_len': 'Average Sentence Length',
            'avg_word_len': 'Average Word Length',
            'ttr': 'Vocabulary Diversity Score',
            'lex_soph': 'Lexical Sophistication',
            'coherence': 'Coherence Score',
            'reasoning_proxy': 'Reasoning Assessment',
            'sentiment_polarity': 'Overall Sentiment',
            'sentiment_subjectivity': 'Subjectivity Score'
        }

        metric_explanations = {
            'word_count': 'Total number of words in the text',
            'sentence_count': 'Total number of complete sentences',
            'avg_sentence_len': 'Words per sentence (ideal: 15-25)',
            'avg_word_len': 'Average characters per word',
            'ttr': 'Ratio of unique words to total words (0-1)',
            'lex_soph': 'Measure of advanced vocabulary usage (0-1)',
            'coherence': 'Text flow and consistency score (0-1)',
            'reasoning_proxy': 'Presence of logical connections (0-1)',
            'sentiment_polarity': 'Sentiment from -1 (negative) to 1 (positive)',
            'sentiment_subjectivity': 'Subjectivity from 0 (objective) to 1 (subjective)'
        }

        for k, v in data.get('diagnostics', {}).items():
            if k not in metric_names:
                continue
            
            # Format values
            if v is None:
                formatted_value = 'N/A'
            elif k in ['avg_sentence_len', 'avg_word_len']:
                formatted_value = f"{v:.2f}"
            elif k in ['ttr', 'lex_soph', 'coherence', 'reasoning_proxy', 'sentiment_polarity', 'sentiment_subjectivity']:
                formatted_value = f"{v:.3f}"
            else:
                formatted_value = str(v)

            # Display with expander
            with st.expander(f"**{metric_names[k]}**: {formatted_value}"):
                st.write(metric_explanations[k])
                
                # Add specific feedback logic
                if k == 'avg_sentence_len' and isinstance(v, (int, float)):
                    if 15 <= v <= 25:
                        st.success("✓ Ideal sentence length for academic writing")
                    elif v < 15:
                        st.warning("Consider combining some shorter sentences")
                    else:
                        st.warning("Consider breaking down some longer sentences")
                
                if k == 'ttr' and v is not None:
                    if v > 0.7:
                        st.success("✓ Excellent vocabulary diversity")
                    elif v > 0.5:
                        st.info("Good vocabulary range")
                    else:
                        st.warning("Consider using more varied vocabulary")
                
                if k == 'coherence' and v is not None:
                    if v > 0.8:
                        st.success("✓ Strong text coherence")
                    elif v > 0.6:
                        st.info("Acceptable coherence")
                    else:
                        st.warning("Consider improving text flow and transitions")

    with tab5:
        st.markdown("### 💭 Sentiment Analysis")
        
        sent1, sent2 = st.columns(2)
        with sent1:
            polarity = data['diagnostics'].get('sentiment_polarity', 0.0)
            st.metric("Sentiment Polarity", f"{polarity:.2f}")
        with sent2:
            subjectivity = data['diagnostics'].get('sentiment_subjectivity', 0.0)
            st.metric("Subjectivity", f"{subjectivity:.2f}")

        # Explanation
        st.info("""
        **Polarity**: -1 (Negative) to +1 (Positive)
        **Subjectivity**: 0 (Objective) to 1 (Subjective)
        """)


# --- Main Execution Flow ---

# Check for OAuth Callback (Global Handler)
if "code" in st.query_params:
    # If already authenticated, just clear the code and continue
    if st.session_state.get('authenticated', False):
        st.query_params.clear()
    else:
        try:
            import google_auth
            user_info = google_auth.get_user_info(st.query_params["code"])
            if user_info:
                st.session_state['authenticated'] = True
                st.session_state['current_user'] = user_info.get('name', 'Google User')
                st.session_state['page'] = 'app'
                st.success(f"Welcome, {user_info.get('name')}!")
                st.query_params.clear()
                st.rerun()
        except Exception as e:
            # If code is invalid (e.g. refresh), just clear it and redirect to login
            st.error(f"Login Failed: {str(e)}")
            st.query_params.clear()
            if "invalid_grant" in str(e):
                st.session_state['page'] = 'login'
                st.rerun()

if st.session_state['page'] == 'landing':
    show_landing_page()
elif st.session_state['page'] == 'login':
    show_login_page()
elif st.session_state['page'] == 'signup':
    show_signup_page()
elif st.session_state['page'] == 'app':
    if st.session_state['authenticated']:
        show_main_app()
    else:
        st.session_state['page'] = 'login'
        st.rerun()
elif st.session_state['page'] == 'profile':
    if st.session_state['authenticated']:
        show_profile_page()
    else:
        st.session_state['page'] = 'login'
        st.rerun()
elif st.session_state['page'] == 'results':
    if st.session_state['authenticated']:
        show_results_page()
    else:
        st.session_state['page'] = 'login'
        st.rerun()
