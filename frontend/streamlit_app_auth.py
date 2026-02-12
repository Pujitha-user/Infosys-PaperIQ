import streamlit as st
import requests
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
from auth import register_user, login_user, add_to_history, get_user_history, delete_history_entry
from document_processor import extract_text_from_file, get_supported_formats

# Page config
st.set_page_config(page_title="PaperIQ", layout="wide", initial_sidebar_state="expanded")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login'

# API configuration
API_URL = os.environ.get("PAPERIQ_API_URL", "http://localhost:8000/analyze")
try:
    API_URL = st.secrets.get("API_URL", API_URL)
except Exception:
    pass


def show_login_page():
    """Display login page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("🧠 PaperIQ")
        st.subheader("AI-Powered Research Insight Analyzer")
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        # LOGIN TAB
        with tab1:
            st.write("**Login to your account**")
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True, key="login_btn"):
                if login_username and login_password:
                    success, message = login_user(login_username, login_password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.session_state.current_page = 'analyzer'
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both username and password")
        
        # SIGNUP TAB
        with tab2:
            st.write("**Create a new account**")
            signup_username = st.text_input("Username", key="signup_username", help="At least 3 characters")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password", help="At least 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            if st.button("Sign Up", use_container_width=True, key="signup_btn"):
                if not signup_username or not signup_email or not signup_password:
                    st.error("All fields are required")
                elif signup_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    success, message = register_user(signup_username, signup_email, signup_password)
                    if success:
                        st.success(message)
                        st.info("You can now login with your credentials!")
                    else:
                        st.error(message)


def show_analyzer_page():
    """Display main analysis page"""
    # Sidebar with user info
    with st.sidebar:
        st.write(f"### 👤 {st.session_state.username}")
        st.markdown("---")
        
        page_selection = st.radio(
            "Navigation",
            ["📝 Analyze", "📚 History"],
            key="nav_radio"
        )
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.current_page = 'login'
            st.rerun()
    
    if page_selection == "📝 Analyze":
        show_analysis_page()
    else:
        show_history_page()


def show_analysis_page():
    """Display the analysis interface"""
    st.title("📄 PaperIQ — AI-Powered Research Insight Analyzer")
    st.markdown("Analyze your paper, essay, or abstract for quality, coherence, and reasoning")
    
    # Input method selection
    input_tab1, input_tab2 = st.tabs(["✍️ Text Input", "📁 File Upload"])
    
    text = None
    
    with input_tab1:
        text = st.text_area("Paste your paper / essay / abstract here", height=300, key="text_input")
    
    with input_tab2:
        st.write("**Upload a document to analyze**")
        supported_formats = get_supported_formats()
        st.info(f"Supported formats: {', '.join([f.upper() for f in supported_formats])}")
        
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=supported_formats,
            help="Upload PDF, DOCX, or TXT files"
        )
        
        if uploaded_file is not None:
            extracted_text, message = extract_text_from_file(uploaded_file)
            st.write(message)
            
            if extracted_text:
                text = extracted_text
                with st.expander("📄 Preview extracted text", expanded=False):
                    st.text_area("Extracted content", extracted_text, height=200, key="preview", disabled=True)
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        analyze_button = st.button("🔍 Analyze", use_container_width=True)
    
    if analyze_button:
        if not text or len(text.strip()) < 20:
            st.warning("⚠️ Please provide at least 20 characters of text (paste or upload a file).")
        else:
            with st.spinner("🔄 Analyzing your text..."):
                try:
                    resp = requests.post(API_URL, json={"text": text}, timeout=15)
                    if resp.status_code != 200:
                        st.error(f"❌ API error: {resp.status_code} - {resp.text}")
                    else:
                        data = resp.json()
                        
                        # Save to history
                        add_to_history(st.session_state.username, text, data)
                        st.success("✅ Analysis saved to your history!")
                        
                        # Display results
                        display_analysis_results(data)
                        
                except Exception as e:
                    st.error(f"❌ Failed to call API: {e}")


def display_analysis_results(data):
    """Display analysis results with visualizations"""
    st.markdown("---")
    st.header("📊 Analysis Results")
    
    # Main scores tab and visualizations tab
    tab1, tab2 = st.tabs(["📊 Scores & Analysis", "📈 Visualizations"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("PaperIQ (composite)", f"{data['composite']}/100")
            st.write(f"**Language:** {data['language']}/100")
            st.write(f"**Coherence:** {data['coherence']}/100")
            st.write(f"**Reasoning (proxy):** {data['reasoning']}/100")
        st.markdown('---')
        st.write('### Detailed Analysis')
        
        # Create a more readable mapping of metric names
        metric_names = {
            'word_count': 'Total Word Count',
            'sentence_count': 'Number of Sentences',
            'avg_sentence_len': 'Average Sentence Length',
            'avg_word_len': 'Average Word Length',
            'ttr': 'Vocabulary Diversity Score',
            'lex_soph': 'Lexical Sophistication',
            'coherence': 'Coherence Score',
            'reasoning_proxy': 'Reasoning Assessment'
        }
        
        # Create a formatted explanation for each metric
        metric_explanations = {
            'word_count': 'Total number of words in the text',
            'sentence_count': 'Total number of complete sentences',
            'avg_sentence_len': 'Words per sentence (ideal: 15-25)',
            'avg_word_len': 'Average characters per word',
            'ttr': 'Ratio of unique words to total words (0-1)',
            'lex_soph': 'Measure of advanced vocabulary usage (0-1)',
            'coherence': 'Text flow and consistency score (0-1)',
            'reasoning_proxy': 'Presence of logical connections (0-1)'
        }

        # Display metrics with better formatting and explanations
        for k, v in data['diagnostics'].items():
            # Skip sentiment fields (not in metric_names)
            if k in ['sentiment_polarity', 'sentiment_subjectivity']:
                continue
            
            # Format the value based on the metric type
            if k in ['avg_sentence_len', 'avg_word_len']:
                formatted_value = f"{v:.2f}"
            elif k in ['ttr', 'lex_soph', 'coherence', 'reasoning_proxy']:
                formatted_value = f"{v:.3f}"
            else:
                formatted_value = str(v)
            
            # Create expander for each metric with details
            with st.expander(f"**{metric_names[k]}**: {formatted_value}"):
                st.write(metric_explanations[k])
                
                # Add contextual feedback
                if k == 'avg_sentence_len':
                    if 15 <= v <= 25:
                        st.success("✓ Ideal sentence length for academic writing")
                    elif v < 15:
                        st.warning("Consider combining some shorter sentences")
                    else:
                        st.warning("Consider breaking down some longer sentences")
                elif k == 'ttr' and v is not None:
                    if v > 0.7:
                        st.success("✓ Excellent vocabulary diversity")
                    elif v > 0.5:
                        st.info("Good vocabulary range")
                    else:
                        st.warning("Consider using more varied vocabulary")
                elif k == 'coherence' and v is not None:
                    if v > 0.8:
                        st.success("✓ Strong text coherence")
                    elif v > 0.6:
                        st.info("Acceptable coherence")
                    else:
                        st.warning("Consider improving text flow and transitions")
        
        with col2:
            st.write('### Top flagged sentences')
            if data['top_flagged_sentences']:
                for s in data['top_flagged_sentences']:
                    st.markdown(f"<div style='background-color:#2e7d32;color:white;padding:8px;border-radius:4px;margin:4px 0'>{s}</div>", unsafe_allow_html=True)
            else:
                st.info("✓ No significant issues found!")
    
    with tab2:
        st.markdown("""
        ### 📈 Analysis Dashboard
        This dashboard provides visual insights into your text's characteristics across multiple dimensions.
        """)

        # Key metrics at the top with explanations
        st.markdown("#### 📊 Key Metrics")
        met1, met2, met3 = st.columns(3)
        with met1:
            st.metric("Total Words", data['diagnostics']['word_count'],
                    help="Total number of words in your text")
        with met2:
            st.metric("Sentence Count", data['diagnostics']['sentence_count'],
                    help="Number of complete sentences detected")
        with met3:
            avg_len = round(data['diagnostics']['avg_sentence_len'], 1)
            st.metric("Avg. Sentence Length", f"{avg_len} words",
                    help="Average number of words per sentence - Good academic writing typically averages 20-25 words")

        # Radar chart with improved design
        st.markdown("#### 🎯 Core Scores Analysis")
        st.markdown("This radar chart shows how your text performs across the three main assessment dimensions.")
        
        scores = {
            'Category': ['Language\nQuality', 'Coherence\n& Flow', 'Reasoning\nStrength'],
            'Score': [data['language'], data['coherence'], data['reasoning']]
        }
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=scores['Score'],
            theta=scores['Category'],
            fill='toself',
            name='Score Distribution',
            fillcolor='rgba(46, 125, 50, 0.5)',
            line=dict(color='#2e7d32', width=2)
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=12),
                    ticksuffix='%'
                ),
                angularaxis=dict(
                    tickfont=dict(size=14, family="Arial, sans-serif")
                )
            ),
            showlegend=False,
            title=dict(
                text='Score Distribution by Category',
                x=0.5,
                y=0.95,
                font=dict(size=20)
            ),
            margin=dict(t=100, b=50),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Advanced metrics with explanations
        st.markdown("#### 📐 Advanced Metrics")
        st.markdown("""
        These metrics provide deeper insight into your text's sophistication and structure.
        Hover over the bars for detailed explanations.
        """)
        
        metric_explanations_adv = {
            'Average Word Length': 'Average number of characters per word. Higher values often indicate more technical/academic language.',
            'Vocabulary Diversity': 'Ratio of unique words to total words (0-1). Higher values show more diverse vocabulary.',
            'Language Sophistication': 'Measure of complex word usage (0-1). Higher values indicate more sophisticated language.'
        }
        
        word_metrics = {
            'Metric': list(metric_explanations_adv.keys()),
            'Value': [
                data['diagnostics']['avg_word_len'],
                data['diagnostics']['ttr'],
                data['diagnostics']['lex_soph']
            ],
            'Explanation': list(metric_explanations_adv.values())
        }
        df = pd.DataFrame(word_metrics)
        
        fig = px.bar(df, 
                    x='Metric', 
                    y='Value',
                    title='Detailed Language Analysis',
                    labels={'Value': 'Score', 'Metric': ''},
                    color_discrete_sequence=['#1e88e5'],
                    custom_data=['Explanation'])
                    
        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>Score: %{y:.2f}<br><br>%{customdata[0]}"
        )
        
        fig.update_layout(
            title=dict(
                font=dict(size=20),
                x=0.5,
                xanchor='center'
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(245,245,245,1)',
            yaxis=dict(
                title="Score",
                tickformat='.2f',
                gridcolor='rgba(200,200,200,0.2)',
                range=[0, max(df['Value']) * 1.2]
            ),
            xaxis=dict(
                title="",
                showgrid=False
            )
        )
        st.plotly_chart(fig, use_container_width=True)


def show_history_page():
    """Display user's analysis history"""
    st.title("📚 Your Analysis History")
    
    history = get_user_history(st.session_state.username)
    
    if not history:
        st.info("📭 No analysis history yet. Start by analyzing some text!")
    else:
        st.write(f"You have **{len(history)}** saved analyses")
        
        # Display history in reverse order (newest first)
        for idx, entry in enumerate(reversed(history)):
            with st.expander(f"📄 {entry['text_preview']} - {entry['timestamp'][:10]}", expanded=False):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write("**Full Text:**")
                    st.write(entry['full_text'])
                    
                    st.markdown("---")
                    st.write("**Analysis Results:**")
                    
                    results = entry['results']
                    score_col1, score_col2, score_col3, score_col4 = st.columns(4)
                    
                    with score_col1:
                        st.metric("Composite", f"{results['composite']}/100")
                    with score_col2:
                        st.metric("Language", f"{results['language']:.1f}/100")
                    with score_col3:
                        st.metric("Coherence", f"{results['coherence']:.1f}/100")
                    with score_col4:
                        st.metric("Reasoning", f"{results['reasoning']:.1f}/100")
                
                with col2:
                    if st.button("🗑️", key=f"delete_{idx}", help="Delete this entry"):
                        if delete_history_entry(st.session_state.username, len(history) - 1 - idx):
                            st.success("Deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete")


# Main app logic
if st.session_state.logged_in:
    show_analyzer_page()
else:
    show_login_page()
