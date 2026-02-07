
from typing import List
from corep_assistant.schemas import TemplateOutput, ValidationFinding, ScenarioFeatures

def validate_data_completeness(output: TemplateOutput, features: ScenarioFeatures) -> List[ValidationFinding]:
    """
    Check for missing values that should have been populated based on scenario data.
    """
    findings = []
    
    # Rule VR_DATA_001_NULL_AMOUNT_WHEN_PROVIDED
    # If mortgage amount provided but 0090:0010 is null
    if features.mortgage_amount_gbp is not None:
        has_0090_0010 = any(
            a.row_code == "0090" and a.col_code == "0010" and a.value is not None 
            for a in output.answers
        )
        if not has_0090_0010:
            findings.append(ValidationFinding(
                severity="WARN",
                rule_id="VR_DATA_001_NULL_AMOUNT_WHEN_PROVIDED",
                message="Scenario provides a mortgage amount but Row 0090 Column 0010 (Original Exposure) is null or missing.",
                impacted_cells=["0090:0010"]
            ))

    # Rule VR_DATA_002_LTV_BLOCKS_RW_ONLY
    # If 0010 or 0040 is null because of LTV missing (incorrect dependency)
    # We detect this if the reasoning mentions LTV for columns 0010/0040
    for answer in output.answers:
        if answer.col_code in ["0010", "0040"] and answer.value is None:
            if "ltv" in (answer.reasoning or "").lower() or "loan-to-value" in (answer.reasoning or "").lower():
                findings.append(ValidationFinding(
                    severity="WARN",
                    rule_id="VR_DATA_002_LTV_BLOCKS_RW_ONLY",
                    message=f"LTV ratio incorrectly cited as reason for null value in Column {answer.col_code}. LTV only blocks Risk Weight (0070) and RWA (0080).",
                    impacted_cells=[f"{answer.row_code}:{answer.col_code}"]
                ))

    return findings
