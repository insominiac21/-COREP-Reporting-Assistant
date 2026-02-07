"""Text normalization while preserving regulatory codes and references"""
import re


def normalize_text(text: str) -> str:
    """
    Clean text lightly while preserving critical regulatory codes.
    
    Preserves:
    - Row codes (0010, 0020, etc.)
    - Template IDs (C 01.00, C01.00, C 07.00, etc.)
    - Article references (Article 112, Article 36(1)(f), etc.)
    - Regulatory references (CRR, CRD, EBA, etc.)
    
    Args:
        text: Raw extracted text
        
    Returns:
        Normalized text
    """
    # Remove excessive whitespace but keep single spaces
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove hyphenation at line breaks (e.g., "regula-\ntory" -> "regulatory")
    # But be careful not to break codes like "C 01.00"
    text = re.sub(r'([a-z])-\s*\n\s*([a-z])', r'\1\2', text)
    
    # Normalize multiple newlines to double newline (paragraph breaks)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Normalize template IDs to consistent format (preserve spacing)
    # C01.00 or C 01.00 -> keep as-is
    
    # Clean up spaces around common punctuation
    text = re.sub(r'\s+([.,;:])', r'\1', text)
    
    # Strip leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def extract_template_id(text: str) -> str:
    """
    Extract template ID from text if present.
    
    Args:
        text: Text to search
        
    Returns:
        Template ID (e.g., "C01.00") or "UNKNOWN"
    """
    # Match patterns like "C 01.00", "C01.00", "C 07.00", etc.
    patterns = [
        r'\bC\s*01\.00\b',
        r'\bC\s*07\.00\b',
        r'\bOF\s*07\.00\b',  # UK variant
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            matched = match.group(0)
            # Normalize to standard format
            if '01' in matched:
                return "C01.00"
            elif '07' in matched:
                return "C07.00"
    
    return "UNKNOWN"


def extract_row_codes(text: str) -> list[str]:
    """
    Extract row codes from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of row codes found
    """
    # Pattern for row codes: 3-4 digit numbers often starting lines or after "Row"
    codes = []
    
    # Pattern 1: "Row 0010" or "Row 0010 -"
    pattern1 = r'\bRow\s+(\d{3,4})\b'
    codes.extend(re.findall(pattern1, text, re.IGNORECASE))
    
    # Pattern 2: Line starting with code
    pattern2 = r'^\s*(\d{3,4})\s+[-–]'
    codes.extend(re.findall(pattern2, text, re.MULTILINE))
    
    return list(set(codes))  # deduplicate


def extract_legal_refs(text: str) -> list[str]:
    """
    Extract legal references from text.
    
    Args:
        text: Text to search
        
    Returns:
        List of legal references found
    """
    refs = []
    
    # Pattern for Article references
    article_pattern = r'Article\s+\d+(?:\(\d+\))?(?:\([a-z]\))?(?:\s+CRR|\s+CRD)?'
    refs.extend(re.findall(article_pattern, text, re.IGNORECASE))
    
    # Pattern for Annex references
    annex_pattern = r'Annex\s+[IVX]+(?:\s+CRR)?'
    refs.extend(re.findall(annex_pattern, text, re.IGNORECASE))
    
    return list(set(refs))  # deduplicate
