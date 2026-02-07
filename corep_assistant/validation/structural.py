"""Structural validation for template outputs"""
from typing import List
from corep_assistant.schemas import TemplateOutput, ValidationFinding
from corep_assistant.schemas.template_registry import load_template_registry, is_valid_cell
from corep_assistant.config import CITATION_STRICT


def validate_structure(output: TemplateOutput) -> List[ValidationFinding]:
    """
    Perform structural validation on template output.
    
    Checks:
    1. Template ID is supported
    2. All row/column codes are valid for the template
    3. All answers have evidence citations (if citation_strict enabled)
    
    Args:
        output: Template output to validate
        
    Returns:
        List of validation findings
    """
    findings = []
    
    # Load registry
    try:
        registry = load_template_registry(output.template_id)
    except ValueError as e:
        findings.append(ValidationFinding(
            severity="FAIL",
            rule_id="VR_STRUCT_001",
            message=f"Invalid template_id: {output.template_id}",
            impacted_cells=[]
        ))
        return findings
    
    allowed_rows = registry["allowed_rows"]
    allowed_cols = registry["allowed_columns"]
    
    # Validate each answer
    for answer in output.answers:
        row_code = answer.row_code
        col_code = answer.col_code
        cell_id = f"{row_code}:{col_code}"
        
        # Check row code
        if row_code not in allowed_rows:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_STRUCT_002",
                message=f"Invalid row code: {row_code} for template {output.template_id}",
                impacted_cells=[cell_id]
            ))
        
        # Check column code
        if col_code not in allowed_cols:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_STRUCT_003",
                message=f"Invalid column code: {col_code} for template {output.template_id}",
                impacted_cells=[cell_id]
            ))
        
        # Check evidence citations
        if CITATION_STRICT and not answer.evidence:
            findings.append(ValidationFinding(
                severity="FAIL",
                rule_id="VR_STRUCT_004",
                message=f"Missing evidence citation for cell {cell_id}",
                impacted_cells=[cell_id]
            ))
        
        # Check if value is populated but evidence is missing
        if answer.value is not None and not answer.evidence:
            findings.append(ValidationFinding(
                severity="WARN",
                rule_id="VR_STRUCT_005",
                message=f"Cell {cell_id} has value but no evidence",
                impacted_cells=[cell_id]
            ))
    
    # If no issues found, add PASS finding
    if not findings:
        findings.append(ValidationFinding(
            severity="PASS",
            rule_id="VR_STRUCT_000",
            message="All structural validation checks passed",
            impacted_cells=[]
        ))
    
    return findings
