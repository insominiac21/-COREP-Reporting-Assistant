"""COREP-aware chunking logic"""
import hashlib
import re
from typing import List, Dict, Optional
from corep_assistant.schemas import Chunk, ChunkMetadata
from .normalize import extract_template_id, extract_row_codes, extract_legal_refs


def generate_chunk_id(
    source_doc: str,
    template_id: str,
    row_code: Optional[str],
    page_start: int,
    text_snippet: str
) -> str:
    """
    Generate deterministic chunk ID.
    
    Args:
        source_doc: Source document name
        template_id: Template identifier
        row_code: Row code if applicable
        page_start: Starting page
        text_snippet: First 80 chars of text
        
    Returns:
        Deterministic chunk ID (hash-based)
    """
    components = [
        source_doc,
        template_id,
        row_code or "NOROW",
        str(page_start),
        text_snippet[:80]
    ]
    
    content = "|".join(components)
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


def detect_chunk_type(text: str, row_codes: List[str]) -> str:
    """
    Detect chunk type based on content patterns.
    
    Args:
        text: Chunk text
        row_codes: Row codes found in text
        
    Returns:
        Chunk type identifier
    """
    text_lower = text.lower()
    
    # Priority order for detection
    if re.search(r'\b(validation rule|rule\s+VR_)', text, re.IGNORECASE):
        return "validation_rule"
    
    if re.search(r'\bcolumn\s+\d{4}\s*[-–]', text, re.IGNORECASE):
        return "column_definition"
    
    if row_codes and re.search(r'\b(row|definition|legal reference)\b', text_lower):
        return "row_definition"
    
    if re.search(r'\b(template scope|general remarks|reporting instructions)\b', text_lower):
        return "template_overview"
    
    return "q_and_a"  # default


def extract_section_from_text(text: str) -> Optional[str]:
    """
    Extract section heading if present.
    
    Args:
        text: Text to search
        
    Returns:
        Section path or None
    """
    # Look for lines with all caps or starting with "="
    lines = text.split('\n')[:5]  # check first 5 lines
    
    for line in lines:
        line = line.strip()
        if line.startswith('='):
            continue
        
        # Check if line is mostly uppercase and meaningful
        if len(line) > 5 and line.isupper():
            return line
    
    return None


def chunk_corep_document(
    pages: List[tuple[int, str]],
    source_doc: str
) -> List[Chunk]:
    """
    Chunk COREP document into semantic chunks.
    
    Strategy:
    - Split on section headers (all-caps lines or === separators)
    - Further split if sections are very long
    - Create row-specific chunks when row definitions detected
    
    Args:
        pages: List of (page_num, text) tuples
        source_doc: Source document filename
        
    Returns:
        List of Chunk objects
    """
    chunks = []
    
    # Combine all pages into one text with page markers
    full_text = ""
    page_map = {}  # character position -> page number
    current_pos = 0
    
    for page_num, page_text in pages:
        page_start_pos = current_pos
        full_text += page_text + "\n\n"
        page_end_pos = len(full_text)
        
        # Map every position in this range to this page
        for pos in range(page_start_pos, page_end_pos):
            page_map[pos] = page_num
        
        current_pos = page_end_pos
    
    # Split on major section markers
    sections = re.split(r'\n={50,}\n', full_text)
    
    for section_text in sections:
        if len(section_text.strip()) < 50:
            continue
        
        # Determine template ID
        template_id = extract_template_id(section_text)
        
        # Try to find row definitions within this section
        row_pattern = r'(Row\s+\d{3,4}\s*[-–][^\n]+(?:\n(?!Row\s+\d)[^\n]+)*)'
        row_matches = list(re.finditer(row_pattern, section_text, re.IGNORECASE | re.MULTILINE))
        
        if row_matches:
            # Create chunks per row
            for match in row_matches:
                row_text = match.group(0).strip()
                row_codes = extract_row_codes(row_text)
                row_code = row_codes[0] if row_codes else None
                
                # Find page range for this chunk
                match_start = match.start()
                match_end = match.end()
                
                # Find absolute positions
                section_start = full_text.find(section_text)
                abs_start = section_start + match_start
                abs_end = section_start + match_end
                
                page_start = page_map.get(abs_start, 1)
                page_end = page_map.get(abs_end, page_start)
                
                # Extract metadata
                legal_refs = extract_legal_refs(row_text)
                section_path = extract_section_from_text(section_text)
                
                chunk_id = generate_chunk_id(
                    source_doc, template_id, row_code, page_start, row_text
                )
                
                metadata = ChunkMetadata(
                    chunk_id=chunk_id,
                    template_id=template_id,
                    chunk_type="row_definition",
                    row_code=row_code,
                    col_code=None,
                    legal_refs=legal_refs,
                    source_doc=source_doc,
                    page_start=page_start,
                    page_end=page_end,
                    section_path=section_path
                )
                
                chunks.append(Chunk(text=row_text, metadata=metadata))
        
        else:
            # Create single chunk for this section
            row_codes = extract_row_codes(section_text)
            row_code = row_codes[0] if row_codes else None
            
            section_start_pos = full_text.find(section_text)
            section_end_pos = section_start_pos + len(section_text)
            
            page_start = page_map.get(section_start_pos, 1)
            page_end = page_map.get(section_end_pos, page_start)
            
            legal_refs = extract_legal_refs(section_text)
            chunk_type = detect_chunk_type(section_text, row_codes)
            section_path = extract_section_from_text(section_text)
            
            chunk_id = generate_chunk_id(
                source_doc, template_id, row_code, page_start, section_text
            )
            
            metadata = ChunkMetadata(
                chunk_id=chunk_id,
                template_id=template_id,
                chunk_type=chunk_type,
                row_code=row_code,
                col_code=None,
                legal_refs=legal_refs,
                source_doc=source_doc,
                page_start=page_start,
                page_end=page_end,
                section_path=section_path
            )
            
            chunks.append(Chunk(text=section_text.strip(), metadata=metadata))
    
    return chunks
