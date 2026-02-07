"""Template registry and schema for C 07.00 - Credit Risk SA"""
from typing import List, Dict

# Allowed row codes for C07.00 (subset for prototype)
C07_ALLOWED_ROWS = [
    "0010",  # Central governments or central banks
    "0020",  # Regional governments or local authorities
    "0030",  # Public sector entities
    "0040",  # Institutions
    "0050",  # Corporates
    "0060",  # Retail
    "0070",  # Equity
    "0080",  # Off-balance sheet exposures not in default
    "0090",  # Retail secured by mortgages - residential
    "0100",  # Retail secured by mortgages - SME
    "0110",  # Other retail
    "0120",  # Exposures in default
    "0130",  # High risk exposures
    "0140",  # Covered bonds
    "0150",  # Equity exposures
    "0160",  # Other items
    "0170",  # Securitisation positions
    "0180",  # Short-term claims on institutions/corporates
    "0190",  # Collective investment undertakings
    "0200",  # Total
    "0290",  # Of which: secured by mortgages - RW 35%
    "0300",  # Of which: secured by mortgages - RW 100%
    "0310",  # Of which: exposures in default - RW 100%
    "0320",  # Of which: exposures in default - RW 150%
]

# Allowed column codes for C07.00
C07_ALLOWED_COLUMNS = [
    "0010",  # Original exposure pre-CCF
    "0040",  # Exposure value
    "0070",  # Risk weight (%)
    "0080",  # Risk-weighted exposure amounts (RWA)
]

# Special row categories
C07_OFF_BALANCE_ROWS = ["0080"]
C07_DEFAULT_ROWS = ["0120", "0310", "0320"]
C07_MORTGAGE_ROWS = ["0090", "0100", "0290", "0300"]
C07_MEMORANDUM_ROWS = ["0290", "0300", "0310", "0320"]

# Exposure class mapping
C07_EXPOSURE_CLASSES = {
    "0010": "Central governments or central banks (Art 112a)",
    "0020": "Regional governments or local authorities (Art 112b)",
    "0040": "Institutions (Art 112c)",
    "0050": "Corporates (Art 112d)",
    "0060": "Retail (Art 112f)",
    "0120": "Exposures in default (Art 127)",
    "0150": "Equity exposures (Art 133)",
    "0170": "Securitisation positions (Art 242-270)",
}

# Template metadata
C07_METADATA = {
    "template_id": "C07.00",
    "template_name": "Credit Risk - Standardised Approach",
    "legal_basis": "Part Three Title II Chapter 2 CRR",
    "reporting_frequency": "Quarterly",
}


def get_c07_cell_ids() -> List[str]:
    """Generate all valid cell IDs for C07.00"""
    cells = []
    for row in C07_ALLOWED_ROWS:
        for col in C07_ALLOWED_COLUMNS:
            cells.append(f"{row}:{col}")
    return cells


def get_c07_registry() -> Dict:
    """Get complete registry for C07.00"""
    return {
        "metadata": C07_METADATA,
        "allowed_rows": C07_ALLOWED_ROWS,
        "allowed_columns": C07_ALLOWED_COLUMNS,
        "cell_ids": get_c07_cell_ids(),
        "off_balance_rows": C07_OFF_BALANCE_ROWS,
        "default_rows": C07_DEFAULT_ROWS,
        "mortgage_rows": C07_MORTGAGE_ROWS,
        "memorandum_rows": C07_MEMORANDUM_ROWS,
        "exposure_classes": C07_EXPOSURE_CLASSES,
    }
