
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class PlannedCell(BaseModel):
    row_code: str
    col_code: str
    status: str  # "fillable", "blocked", "unknown"
    dependency: List[str]
    missing_input: Optional[str] = None

def compute_cell_plan(template_id: str, row_code: str, features: Any) -> List[PlannedCell]:
    """
    Determine which columns are fillable or blocked based on scenario features.
    
    C07.00 Row 0090 Example:
    - 0010: Nominal Amount -> fillable if mortgage_amount_gbp present
    - 0040: Exposure Value -> fillable if 0010 is present (and no CRM/CCF needed or provided)
    - 0070: Risk Weight -> blocked if LTV missing
    - 0080: RWA -> blocked if RW is blocked
    """
    plan = []
    
    if template_id == "C07.00":
        if row_code == "0090":
            # Column 0010: Original Exposure
            if features.mortgage_amount_gbp is not None:
                plan.append(PlannedCell(
                    row_code=row_code, col_code="0010", 
                    status="fillable", dependency=["mortgage_amount_gbp"]
                ))
            else:
                plan.append(PlannedCell(
                    row_code=row_code, col_code="0010", 
                    status="blocked", dependency=["mortgage_amount_gbp"],
                    missing_input="Mortgage portfolio amount"
                ))
            
            # Column 0040: Exposure Value
            # For now, if we have 0010 and it's on-balance (default for mortgages here), it's fillable
            plan.append(PlannedCell(
                row_code=row_code, col_code="0040", 
                status="fillable", dependency=["mortgage_amount_gbp", "no_crm_adjustment"]
            ))
            
            # Column 0070: Risk Weight
            # Blocked by LTV (which we don't have a specific feature for yet, so we'll check if suggested_risk_weight is None and no LTV mention)
            # In our prototype, we'll assume LTV is always needed for Row 0090 unless suggested_risk_weight provided.
            if features.suggested_risk_weight is not None:
                plan.append(PlannedCell(
                    row_code=row_code, col_code="0070", 
                    status="fillable", dependency=["suggested_risk_weight"]
                ))
            else:
                plan.append(PlannedCell(
                    row_code=row_code, col_code="0070", 
                    status="blocked", dependency=["ltv_ratio"],
                    missing_input="LTV ratio / property type"
                ))
            
            # Column 0080: RWA
            if features.suggested_risk_weight is not None and features.mortgage_amount_gbp is not None:
                 plan.append(PlannedCell(
                    row_code=row_code, col_code="0080", 
                    status="fillable", dependency=["0010", "0070"]
                ))
            else:
                plan.append(PlannedCell(
                    row_code=row_code, col_code="0080", 
                    status="blocked", dependency=["0070"],
                    missing_input="Risk weight (blocked by LTV)"
                ))
    
    return plan
