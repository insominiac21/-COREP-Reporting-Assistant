"""PDF text extraction with page number preservation"""
import re
from pathlib import Path
from typing import List, Tuple
import pypdf


def extract_pdf_text(pdf_path: Path) -> List[Tuple[int, str]]:
    """
    Extract text from PDF preserving page numbers.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of (page_number, text) tuples (1-indexed)
    """
    pages = []
    
    try:
        with open(pdf_path, 'rb') as f:
            reader = pypdf.PdfReader(f)
            
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Page numbers are 1-indexed
                pages.append((page_num + 1, text))
                
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return []
    
    return pages


def extract_text_file(text_path: Path) -> List[Tuple[int, str]]:
    """
    Extract text from .txt file, treating it as single-page.
    
    Args:
        text_path: Path to text file
        
    Returns:
        List with single (page_number, text) tuple
    """
    try:
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return [(1, text)]
    except Exception as e:
        print(f"Error reading text file {text_path}: {e}")
        return []


def extract_document(doc_path: Path) -> List[Tuple[int, str]]:
    """
    Extract text from document (PDF or TXT).
    
    Args:
        doc_path: Path to document
        
    Returns:
        List of (page_number, text) tuples
    """
    suffix = doc_path.suffix.lower()
    
    if suffix == '.pdf':
        return extract_pdf_text(doc_path)
    elif suffix == '.txt':
        return extract_text_file(doc_path)
    else:
        print(f"Unsupported file type: {suffix}")
        return []
