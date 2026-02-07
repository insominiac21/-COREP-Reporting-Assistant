"""C01.00 arithmetic validation checks"""
from typing import List, Dict, Optional
from corep_assistant.schemas import TemplateOutput, ValidationFinding, AnswerItem, ScenarioFeatures

# Known deduction rows in C01.00 that must be negative (as per prototype and instruction)
C01_DEDUCTION_ROWS = ["0070", "0290", "0300"]

def get_answer_value(answers: List[AnswerItem], row_code: str) -> Optional[float]:
    """Get value for a specific row code"""
    for answer in answers:
        if answer.row_code == row_code and answer.value is not None:
            return answer.value
    return None


def validate_c01_arithmetic(output: TemplateOutput, features: ScenarioFeatures) -> List[ValidationFinding]:
    """
    Validate C01.00 arithmetic rules.
    
    Rules:
    1. Own funds (0010) = Tier 1 (0060) + Tier 2 (0200)
    2. Tier 1 (0060) = CET1 (0050) + AT1 (0140)
    3. VR_C01_003: Deduction sign check (escalate to FAIL if user sign wrong)
    
    Args:
        output: Template output
        features: Scenario features
        
    Returns:
        List of validation findings
    """
    if output.template_id != "C01.00":
        return []
    
    findings = []
    answers = output.answers
    
    # Rule 1: Own funds = Tier 1 + Tier 2
    own_funds = get_answer_value(answers, "0010")
    tier1 = get_answer_value(answers, "0060") or get_answer_value(answers, "0020")
    tier2 = get_answer_value(answers, "0200")
    
    if own_funds is not None and tier1 is not None and tier2 is not None:
        expected = tier1 + tier2
        tolerance = abs(expected) * 0.01  # 1% tolerance for rounding
        
        if abs(own_funds - expected) > tolerance:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_C01_001",
                message=f"Own funds (0010:0010) = {own_funds} but Tier1 + Tier2 = {expected}",
                impacted_cells=["0010:0010", "0060:0010", "0200:0010"]
            ))
        else:
            findings.append(ValidationFinding(
                severity="PASS",
                rule_id="VR_C01_001",
                message="Own funds = Tier 1 + Tier 2 (validated)",
                impacted_cells=[]
            ))
    elif own_funds is not None or tier1 is not None or tier2 is not None:
        findings.append(ValidationFinding(
            severity="WARN",
            rule_id="VR_C01_001",
            message="Cannot validate own funds formula: missing components",
            impacted_cells=[]
        ))
    
    # Rule 2: Tier 1 = CET1 + AT1
    cet1 = get_answer_value(answers, "0050")
    at1 = get_answer_value(answers, "0140")
    
    if tier1 is not None and cet1 is not None and at1 is not None:
        expected = cet1 + at1
        tolerance = abs(expected) * 0.01
        
        if abs(tier1 - expected) > tolerance:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_C01_002",
                message=f"Tier 1 (0060:0010) = {tier1} but CET1 + AT1 = {expected}",
                impacted_cells=["0060:0010", "0050:0010", "0140:0010"]
            ))
        else:
            findings.append(ValidationFinding(
                severity="PASS",
                rule_id="VR_C01_002",
                message="Tier 1 = CET1 + AT1 (validated)",
                impacted_cells=[]
            ))
    elif tier1 is not None:
        # If Tier 1 is present but components missing, specialize the skip message
        missing = []
        if cet1 is None: missing.append("CET1 (0050)")
        if at1 is None: missing.append("AT1 (0140)")
        
        findings.append(ValidationFinding(
            severity="WARN",
            rule_id="VR_C01_002",
            message=f"Tier 1 validation skipped because {', '.join(missing)} not provided",
            impacted_cells=[]
        ))

    # Rule 3: VR_C01_003: Deduction sign check
    for answer in answers:
        if answer.row_code in C01_DEDUCTION_ROWS:
            cell_id = f"{answer.row_code}:{answer.col_code}"
            if answer.value is not None and answer.value > 0:
                # If it's a recognized deduction but positive, it's a sign issue.
                # Escalate to FAIL because deductions MUST reduce capital.
                findings.append(ValidationFinding(
                    severity="FAIL",
                    rule_id="VR_C01_003",
                    message=f"Deduction item {cell_id} must be negative (found {answer.value})",
                    impacted_cells=[cell_id]
                ))
            elif answer.value is not None and answer.value < 0:
                findings.append(ValidationFinding(
                    severity="PASS",
                    rule_id="VR_C01_003",
                    message=f"Deduction item {cell_id} correctly applied as negative",
                    impacted_cells=[cell_id]
                ))
    
    return findings
