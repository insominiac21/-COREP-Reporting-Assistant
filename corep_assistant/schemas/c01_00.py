"""Template registry and schema for C 01.00 - Own Funds"""
from typing import List, Dict

# Allowed row codes for C01.00 (subset for prototype)
C01_ALLOWED_ROWS = [
    "0010",  # Own funds total
    "0020",  # Tier 1 capital (also 0060 in some versions)
    "0030",  # CET1 capital instruments
    "0040",  # Share premium accounts
    "0050",  # Common Equity Tier 1 capital total
    "0060",  # Tier 1 capital total
    "0070",  # Own CET1 instruments held
    "0080",  # Direct holdings of CET1 of financial sector entities
    "0090",  # Indirect holdings of CET1 of financial sector entities
    "0100",  # Synthetic holdings of CET1 of financial sector entities
    "0110",  # Deferred tax assets dependent on future profitability
    "0120",  # Fair value reserves related to gains/losses on cash flow hedges
    "0130",  # Retained earnings
    "0140",  # Additional Tier 1 capital total
    "0150",  # AT1 capital instruments
    "0160",  # Share premium accounts for AT1
    "0170",  # Own AT1 instruments held
    "0180",  # Direct holdings of AT1 of financial sector entities
    "0190",  # Indirect holdings of AT1 of financial sector entities
    "0200",  # Tier 2 capital total
    "0210",  # T2 capital instruments
    "0220",  # Share premium accounts for T2
    "0230",  # Own T2 instruments held
    "0240",  # Direct holdings of T2 of financial sector entities
    "0250",  # Indirect holdings of T2 of financial sector entities
    "0290",  # Prudent valuation adjustments / AVAs
    "0300",  # Goodwill
]

# Allowed column codes for C01.00
C01_ALLOWED_COLUMNS = [
    "0010",  # Amount
]

# Row dependencies for arithmetic validation
C01_ARITHMETIC_RULES = {
    "own_funds_formula": {
        "target": "0010",
        "components": ["0060", "0200"],  # Tier1 + Tier2
        "operation": "sum",
    },
    "tier1_formula": {
        "target": "0060",
        "components": ["0050", "0140"],  # CET1 + AT1
        "operation": "sum",
    },
}

# Template metadata
C01_METADATA = {
    "template_id": "C01.00",
    "template_name": "Own Funds",
    "legal_basis": "Part Two CRR",
    "reporting_frequency": "Quarterly",
}


def get_c01_cell_ids() -> List[str]:
    """Generate all valid cell IDs for C01.00"""
    cells = []
    for row in C01_ALLOWED_ROWS:
        for col in C01_ALLOWED_COLUMNS:
            cells.append(f"{row}:{col}")
    return cells


def get_c01_registry() -> Dict:
    """Get complete registry for C01.00"""
    return {
        "metadata": C01_METADATA,
        "allowed_rows": C01_ALLOWED_ROWS,
        "allowed_columns": C01_ALLOWED_COLUMNS,
        "cell_ids": get_c01_cell_ids(),
        "arithmetic_rules": C01_ARITHMETIC_RULES,
    }
