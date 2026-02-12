"""
Document processing utilities for PaperIQ
Supports: PDF, DOCX, TXT
"""
import io
from typing import Optional

try:
    import PyPDF2
    PDF_SUPPORTED = True
except ImportError:
    PDF_SUPPORTED = False

try:
    import docx
    DOCX_SUPPORTED = True
except ImportError:
    DOCX_SUPPORTED = False


def extract_text_from_pdf(file_bytes: bytes) -> Optional[str]:
    """Extract text from PDF file"""
    if not PDF_SUPPORTED:
        return None
    
    try:
        pdf_file = io.BytesIO(file_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return None


def extract_text_from_docx(file_bytes: bytes) -> Optional[str]:
    """Extract text from DOCX file"""
    if not DOCX_SUPPORTED:
        return None
    
    try:
        doc_file = io.BytesIO(file_bytes)
        doc = docx.Document(doc_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return None


def extract_text_from_txt(file_bytes: bytes) -> Optional[str]:
    """Extract text from TXT file"""
    try:
        return file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            return file_bytes.decode('latin-1')
        except Exception as e:
            print(f"Error extracting TXT: {e}")
            return None


def extract_text_from_file(uploaded_file) -> tuple[Optional[str], str]:
    """
    Extract text from uploaded file based on file type
    Returns: (text, message)
    """
    if uploaded_file is None:
        return None, "No file uploaded"
    
    file_bytes = uploaded_file.read()
    file_name = uploaded_file.name.lower()
    
    # Detect file type and extract text
    if file_name.endswith('.pdf'):
        if not PDF_SUPPORTED:
            return None, "PDF support not available. Install PyPDF2: pip install PyPDF2"
        text = extract_text_from_pdf(file_bytes)
        if text:
            return text, f"✅ Extracted {len(text)} characters from PDF"
        else:
            return None, "❌ Failed to extract text from PDF"
    
    elif file_name.endswith('.docx'):
        if not DOCX_SUPPORTED:
            return None, "DOCX support not available. Install python-docx: pip install python-docx"
        text = extract_text_from_docx(file_bytes)
        if text:
            return text, f"✅ Extracted {len(text)} characters from DOCX"
        else:
            return None, "❌ Failed to extract text from DOCX"
    
    elif file_name.endswith('.txt'):
        text = extract_text_from_txt(file_bytes)
        if text:
            return text, f"✅ Extracted {len(text)} characters from TXT"
        else:
            return None, "❌ Failed to extract text from TXT"
    
    else:
        return None, f"❌ Unsupported file type. Please upload PDF, DOCX, or TXT files."


def get_supported_formats() -> list[str]:
    """Get list of supported file formats"""
    formats = ['txt']
    if PDF_SUPPORTED:
        formats.append('pdf')
    if DOCX_SUPPORTED:
        formats.append('docx')
    return formats
