
import re
from typing import Dict, Optional

def extract_amounts(text: str) -> Dict[str, float]:
    """
    Extract various amounts from scenario text based on context.
    
    Returns a dictionary of found amounts:
    {
        "mortgage_amount_gbp": 150000000.0,
        "exposure_amount_gbp": 10000000.0,
        "nominal_amount_gbp": 80000000.0
    }
    """
    found = {}
    
    # Text pre-processing
    text_lower = text.lower()
    
    def parse_num(val_str: str, suffix: str) -> float:
        val = float(val_str.replace(',', ''))
        if suffix:
            suffix = suffix.lower()
            if suffix in ['m', 'million']:
                return val * 1_000_000
            elif suffix in ['k', 'thousand']:
                return val * 1_000
            elif suffix in ['b', 'billion']:
                return val * 1_000_000_000
        return val

    # Regex for numbers with optional suffixes
    num_pattern = r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)\s*(m|million|k|thousand|b|billion)?'
    
    # 1. Mortgage / Portfolio detection
    mortgage_match = re.search(
        rf'(?:mortgage|residential|portfolio|first lien)\s+(?:portfolio|amount|of|nominal)?\s*(?:of|is|at)?\s*{num_pattern}', 
        text_lower
    )
    if mortgage_match:
        found["mortgage_amount_gbp"] = parse_num(mortgage_match.group(1), mortgage_match.group(2))
    
    # 2. Exposure detection
    exposure_match = re.search(
        rf'(?:exposure|derivative|otc)\s+(?:amount|of|nominal)?\s*(?:of|is|at)?\s*{num_pattern}', 
        text_lower
    )
    if exposure_match:
        found["exposure_amount_gbp"] = parse_num(exposure_match.group(1), exposure_match.group(2))

    # 3. Nominal detection
    nominal_match = re.search(
        rf'nominal\s+(?:amount|of)?\s*(?:of|is|at)?\s*{num_pattern}', 
        text_lower
    )
    if nominal_match:
        found["nominal_amount_gbp"] = parse_num(nominal_match.group(1), nominal_match.group(2))

    # Backup: Look for large numbers if nothing specific found
    if not found:
        # Just find all numbers and pick the largest as a candidate if context ambiguous?
        # Better to be safe and only extract with context.
        pass

    return found
