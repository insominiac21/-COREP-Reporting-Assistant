"""Scenario feature extraction for validation rules"""
import re
from typing import Optional
from corep_assistant.schemas import ScenarioFeatures

def extract_suggested_risk_weight(text: str) -> Optional[float]:
    """
    Extract suggested risk weight percentage from text.
    Matches: "20% risk weight", "risk weight of 20%", "RW 20%", "suggests 20%"
    """
    # Look for patterns like:
    # - 20% risk weight
    # - risk weight (of) 20%
    # - RW 20%
    # - 20% bucket
    
    text = text.lower()
    
    # Regex for percentage followed by relevant keywords
    # e.g. "20% risk weight", "20% rw"
    pattern1 = r"(\d+(?:\.\d+)?)%\s*(?:risk\s*weight|rw|bucket)"
    match1 = re.search(pattern1, text)
    if match1:
        return float(match1.group(1))
        
    # Regex for keywords followed by percentage
    # e.g. "risk weight 20%", "rw of 20%"
    pattern2 = r"(?:risk\s*weight|rw|bucket)\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)%"
    match2 = re.search(pattern2, text)
    if match2:
        return float(match2.group(1))
        
    # Regex for "suggests X%" where X is clearly a RW
    pattern3 = r"suggests?\s+(\d+(?:\.\d+)?)%"
    match3 = re.search(pattern3, text)
    if match3:
        return float(match3.group(1))
        
    return None

def extract_flags(text: str) -> dict:
    """Extract boolean flags from scenario text"""
    text = text.lower()
    
    flags = {
        "is_default": False,
        "is_off_balance": False
    }
    
    # Default triggers - STRICTER
    # Must match "in default", "past due", "unlikely to pay", "article 178"
    # plain "default" is too risky (e.g. "default values", "no default")
    default_keywords_regex = [
        r"\bin default\b", 
        r"\bpast due\b", 
        r"\bunlikely to pay\b", 
        r"\barticle 178\b", 
        r"\bdefaulted\b", 
        r"\bnon-performing\b"
    ]
    
    if any(re.search(pattern, text) for pattern in default_keywords_regex):
        flags["is_default"] = True
        
    # Off-balance triggers
    # Avoiding negated terms like "no guarantee", "without guarantee"
    off_balance_keywords = [
        "off-balance", "loan commitment", 
        "credit line", "letter of credit"
    ]
    
    if any(k in text for k in off_balance_keywords):
        flags["is_off_balance"] = True
        
    # Special check for guarantee to avoid negation
    # Matches "guarantee" but NOT if preceded by "no ", "without ", "neither "
    if "guarantee" in text:
        # Regex: negative lookbehind for "no ", "without ", "neither " 
        # allowing for some whitespace
        # \b ensures we match whole word "guarantee"
        # (?<!...) is negative lookbehind
        no_guarantee_pattern = r"(?<!no\s)(?<!without\s)(?<!neither\s)\bguarantee"
        if re.search(no_guarantee_pattern, text):
            flags["is_off_balance"] = True
            
    return flags

from corep_assistant.scenario.amounts import extract_amounts


def parse_scenario(text: str) -> ScenarioFeatures:
    """Parse scenario text into structured features including amounts"""
    if not text:
        return ScenarioFeatures()
        
    flags = extract_flags(text)
    suggested_rw = extract_suggested_risk_weight(text)
    amounts = extract_amounts(text)
    
    return ScenarioFeatures(
        is_default=flags["is_default"],
        is_off_balance=flags["is_off_balance"],
        suggested_risk_weight=suggested_rw,
        **amounts
    )
