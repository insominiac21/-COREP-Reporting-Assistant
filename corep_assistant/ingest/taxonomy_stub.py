"""Taxonomy stub for DPM/XBRL ingestion (future extension)"""
from typing import Optional, Dict


def parse_dpm_artifact(dpm_path: str) -> Optional[Dict]:
    """
    Stub for parsing DPM (Data Point Model) artifacts.
    
    Future implementation would:
    - Parse DPM XML/Excel files
    - Extract business concepts and relationships
    - Map to template registry structures
    
    Args:
        dpm_path: Path to DPM artifact file
        
    Returns:
        Dictionary with parsed concepts or None
    """
    print(f"DPM parsing not yet implemented for: {dpm_path}")
    return None


def parse_xbrl_taxonomy(taxonomy_path: str) -> Optional[Dict]:
    """
    Stub for parsing XBRL taxonomy files.
    
    Future implementation would:
    - Parse XBRL schema (.xsd) and linkbase files
    - Extract dimension definitions
    - Map validation formulas to validation rules
    
    Args:
        taxonomy_path: Path to XBRL taxonomy directory
        
    Returns:
        Dictionary with parsed taxonomy or None
    """
    print(f"XBRL parsing not yet implemented for: {taxonomy_path}")
    return None


def extend_registry_from_taxonomy(template_id: str, taxonomy_data: Dict) -> bool:
    """
    Stub for extending template registry from parsed taxonomy.
    
    Future implementation would:
    - Merge taxonomy definitions into registry
    - Update allowed rows/columns dynamically
    - Import validation formulas
    
    Args:
        template_id: Template to extend
        taxonomy_data: Parsed taxonomy data
        
    Returns:
        True if successful
    """
    print(f"Registry extension not yet implemented for template: {template_id}")
    return False
