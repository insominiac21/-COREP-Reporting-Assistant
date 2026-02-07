"""C07.00 specific validation rules"""
from typing import List
from corep_assistant.schemas import TemplateOutput, ValidationFinding, ScenarioFeatures
from corep_assistant.schemas.c07_00 import C07_OFF_BALANCE_ROWS, C07_DEFAULT_ROWS, C07_MEMORANDUM_ROWS


def validate_c07_rules(output: TemplateOutput, features: ScenarioFeatures) -> List[ValidationFinding]:
    """
    Validate C07.00 specific rules using extracted features.
    
    Rules:
    1. If scenario is off-balance, row 0080 should be used
    2. If scenario is default, default rows should be used
    3. Memorandum rows should not be in total calculations
    4. RWA = exposure value * risk weight (with tolerance)
    5. VR_C07_RW_DEFAULT_CONTRADICTION: Check for conflicting suggested RW for default
    6. VR_C07_DEFAULT_RW_UNDETERMINED: Check if provisions needed for 100/150% RW extraction
    """
    if output.template_id != "C07.00":
        return []
    
    findings = []
    
    # Get populated row codes
    populated_rows = set(answer.row_code for answer in output.answers)
    
    # Rule 1: Off-balance sheet check
    if features.is_off_balance:
        if not any(row in populated_rows for row in C07_OFF_BALANCE_ROWS):
            findings.append(ValidationFinding(
                severity="WARN",
                rule_id="VR_C07_001",
                message="Scenario indicates off-balance sheet exposure but row 0080 not populated",
                impacted_cells=[]
            ))
        else:
            findings.append(ValidationFinding(
                severity="PASS",
                rule_id="VR_C07_001",
                message="Off-balance sheet exposure correctly mapped to row 0080",
                impacted_cells=[]
            ))
    
    # Rule 2: Default exposure check
    # ONLY if scenario is explicitly default
    if features.is_default:
        if not any(row in populated_rows for row in C07_DEFAULT_ROWS):
            findings.append(ValidationFinding(
                severity="WARN",
                rule_id="VR_C07_002",
                message="Scenario indicates default exposure but default rows not populated (should be row 0120)",
                impacted_cells=[]
            ))
        else:
            findings.append(ValidationFinding(
                severity="PASS",
                rule_id="VR_C07_DEFAULT_ROW_MAPPING",
                message="Default exposure correctly mapped to default rows",
                impacted_cells=[]
            ))
    
    # New Rule: VR_C07_RW_DEFAULT_CONTRADICTION
    # Only run if is_default is TRUE
    if features.is_default and features.suggested_risk_weight is not None:
        # Default exposures are usually 100% or 150%. 
        # If user suggests 0, 20, 50, 75, etc., it's likely a contradiction.
        # We flag clearly non-default RWs.
        suggested = features.suggested_risk_weight
        if suggested in [0, 20, 50, 75]:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_C07_RW_DEFAULT_CONTRADICTION",
                message=f"Suggested RW {suggested}% conflicts with default exposure treatment; default exposures are RW 100% or 150% depending on provisions.",
                impacted_cells=["0120:0010"]  # Attach to Amount column as proxy if RW col unknown
            ))
            
    # New Rule: VR_C07_DEFAULT_RW_UNDETERMINED
    # Run ONLY if default is TRUE
    if features.is_default:
        # Check if we have evidence or input about provisions? 
        # Actually checking if we found a "provisions" amount is hard with current parser.
        # But we can add a general guidance warning.
        findings.append(ValidationFinding(
            severity="WARN",
            rule_id="VR_C07_DEFAULT_RW_UNDETERMINED",
            message="Cannot determine 100% vs 150% RW without provisions level; provide provisions amount or %.",
            impacted_cells=["0120:0010"]
        ))

    # Rule 3: Check for Memorandum row usage
    memo_rows_used = [row for row in populated_rows if row in C07_MEMORANDUM_ROWS]
    if memo_rows_used:
        findings.append(ValidationFinding(
            severity="PASS",
            rule_id="VR_C07_003",
            message=f"Memorandum rows used: {', '.join(memo_rows_used)} (ensure not double-counted in totals)",
            impacted_cells=[f"{row}:0010" for row in memo_rows_used]
        ))
    
    # Rule 4: RWA calculation check
    for answer in output.answers:
        if answer.col_code == "0080":  # RWA column
            # Find corresponding exposure value and risk weight
            exposure_answer = next(
                (a for a in output.answers 
                 if a.row_code == answer.row_code and a.col_code == "0040"),
                None
            )
            rw_answer = next(
                (a for a in output.answers 
                 if a.row_code == answer.row_code and a.col_code == "0070"),
                None
            )
            
            if exposure_answer and rw_answer and exposure_answer.value and rw_answer.value:
                expected_rwa = exposure_answer.value * (rw_answer.value / 100.0)
                tolerance = abs(expected_rwa) * 0.02  # 2% tolerance
                
                if answer.value and abs(answer.value - expected_rwa) > tolerance:
                    cell_id = f"{answer.row_code}:0080"
                    findings.append(ValidationFinding(
                        severity="WARN",
                        rule_id="VR_C07_004",
                        message=f"RWA ({cell_id}) = {answer.value} but exposure * RW = {expected_rwa}",
                        impacted_cells=[cell_id]
                    ))
    
    return findings
