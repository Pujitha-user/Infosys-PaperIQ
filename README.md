# 🧠 PaperIQ - AI-Powered Research Insight Analyzer

An intelligent text analysis system that evaluates research papers, essays, and abstracts using AI-powered quality metrics. Features user authentication, document processing, and comprehensive analysis visualization.

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)

## ✨ Features

### 🔐 Authentication System
- **User Registration** - Create new accounts with email and password
- **Secure Login** - Password hashing with SHA256
- **Session Management** - Persistent login state

### 📄 Document Analysis
- **Text Input** - Direct paste text for analysis
- **File Upload Support** - Upload PDF, DOCX, or TXT files
- **Multi-dimensional Scoring**:
  - Language Quality (vocabulary, sophistication)
  - Coherence & Flow (consistency, structure)
  - Reasoning Assessment (logical connections)
  - Composite Score (overall quality)

### 📊 Visualizations
- **Interactive Radar Charts** - Score distribution across dimensions
- **Bar Charts** - Detailed metrics breakdown
- **Metrics Dashboard** - Key statistics and insights
- **Contextual Feedback** - Actionable suggestions for improvement

### 📚 History Tracking
- **Analysis History** - Automatic storage of all analyses
- **History Browser** - View past analyses with full details
- **History Management** - Delete individual entries
- **Persistent Storage** - JSON-based database

### 🎨 User Interface
- **Dark Theme** - Eye-friendly dark mode
- **Responsive Design** - Works on all screen sizes
- **Intuitive Navigation** - Sidebar with user profile
- **Progress Indicators** - Loading spinners and status messages

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Pujitha-user/Infosys-PaperIQ.git
cd Infosys-PaperIQ
```

2. **Create virtual environment**
```bash
python -m venv .venv
```

3. **Activate virtual environment**
```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

4. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Running the Application

#### Start Backend API
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

#### Start Frontend (with authentication)
```bash
streamlit run frontend/streamlit_app_auth.py --server.port=8501
```

#### Alternative: Run without authentication
```bash
streamlit run frontend/streamlit_app.py --server.port=8501
```

#### Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage Guide

### 1. Create an Account
- Navigate to http://localhost:8501
- Click the "Sign Up" tab
- Enter username (min 3 characters), email, and password (min 6 characters)
- Click "Sign Up" button

### 2. Login
- Click the "Login" tab
- Enter your username and password
- Click "Login" button

### 3. Analyze Text

#### Option A: Direct Text Input
- Navigate to "Analyze" section
- Click "Text Input" tab
- Paste your text (minimum 20 characters)
- Click "🔍 Analyze" button

#### Option B: File Upload
- Navigate to "Analyze" section
- Click "File Upload" tab
- Click "Choose a file"
- Select PDF, DOCX, or TXT file
- Preview extracted text (optional)
- Click "🔍 Analyze" button

### 4. View Results
- Review composite score and dimension scores
- Explore detailed metrics in expandable sections
- Check visualizations in the "Visualizations" tab
- View flagged sentences and suggestions

### 5. Access History
- Click "History" in the sidebar navigation
- Browse all past analyses
- View full text and scores for each entry
- Delete entries using the 🗑️ button

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── main.py          # API endpoints and analysis logic
└── __pycache__/     # Python cache (excluded from git)
```

**Key Endpoints:**
- `GET /health` - Health check
- `POST /analyze` - Text analysis endpoint

### Frontend (Streamlit)
```
frontend/
├── streamlit_app_auth.py    # Main authenticated app
├── streamlit_app.py         # Simple app (no auth)
├── auth.py                  # Authentication logic
├── document_processor.py    # File processing
├── google_auth.py          # OAuth integration (optional)
└── data/                   # User data (excluded from git)
    ├── users.json          # User credentials
    └── history.json        # Analysis history
```

### Configuration
```
.streamlit/
└── config.toml     # Theme and app settings
```

## 📊 Analysis Metrics

### Language Quality (40% weight)
- **Type-Token Ratio (TTR)** - Vocabulary diversity
- **Lexical Sophistication** - Complex word usage
- **Average Word Length** - Technical language indicator

### Coherence Score (30% weight)
- **Sentence Length Variance** - Structural consistency
- **Flow Assessment** - Text smoothness

### Reasoning Assessment (30% weight)
- **Causal Connectors** - Logical transitions
- **Modal Verbs** - Argument strength
- **Reasoning Patterns** - Critical thinking indicators

## 🔧 Configuration

### Environment Variables
```bash
# API URL (optional)
PAPERIQ_API_URL=http://localhost:8000/analyze
```

### Theme Customization
Edit `.streamlit/config.toml`:
```toml
[theme]
base="dark"
primaryColor="#2e7d32"
backgroundColor="#0e1117"
secondaryBackgroundColor="#161b22"
textColor="#c9d1d9"
```

## 📦 Dependencies

### Core
- **fastapi** - Backend API framework
- **uvicorn** - ASGI server
- **streamlit** - Frontend framework
- **pydantic** - Data validation

### Analysis
- **textblob** - NLP and sentiment analysis
- **transformers** - Advanced NLP models
- **torch** - Deep learning framework
- **sentence-transformers** - Semantic analysis

### Document Processing
- **PyPDF2** - PDF text extraction
- **python-docx** - Word document processing

### Visualization
- **plotly** - Interactive charts
- **pandas** - Data manipulation
- **numpy** - Numerical operations

## 🛡️ Security

- **Password Hashing** - SHA256 encryption
- **Session Management** - Secure state handling
- **Input Validation** - Backend/frontend validation
- **Data Isolation** - User-specific history

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Team-Infotech** - Initial development
- **Pujitha** - Repository maintainer

## 🙏 Acknowledgments

- Built with FastAPI and Streamlit
- NLP powered by TextBlob and Transformers
- Visualization using Plotly

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`

## 🔄 Version History

### v1.0.0 (Current)
- ✅ User authentication system
- ✅ File upload support (PDF, DOCX, TXT)
- ✅ Analysis history tracking
- ✅ Dark theme UI
- ✅ Interactive visualizations
- ✅ Multi-dimensional text analysis
- ✅ RESTful API backend

---

**Made with ❤️ using Python, FastAPI, and Streamlit**