"""Validation report merger"""
from typing import List, Dict, Any
from corep_assistant.schemas import TemplateOutput, ValidationFinding
from .structural import validate_structure
from .c01_math import validate_c01_arithmetic
from .c07_rules import validate_c07_rules
from .scenario_parse import parse_scenario
from .data_completeness import validate_data_completeness


def run_all_validations(
    output: TemplateOutput,
    scenario: str = ""
) -> Dict[str, Any]:
    """
    Run all validation checks and merge findings.
    
    Args:
        output: Template output to validate
        scenario: User scenario (needed for C07 context checks)
        
    Returns:
        Validation report dictionary
    """
    all_findings: List[ValidationFinding] = []
    
    # Parse scenario features
    scenario_features = parse_scenario(scenario)
    
    # 1. Structural validation (always)
    structural_findings = validate_structure(output)
    all_findings.extend(structural_findings)
    
    # 2. Data completeness validation (new)
    completeness_findings = validate_data_completeness(output, scenario_features)
    all_findings.extend(completeness_findings)

    # 3. Template-specific validation
    if output.template_id == "C01.00":
        c01_findings = validate_c01_arithmetic(output, scenario_features)
        all_findings.extend(c01_findings)
    elif output.template_id == "C07.00":
        c07_findings = validate_c07_rules(output, scenario_features)
        all_findings.extend(c07_findings)
    
    # Count by severity
    severity_counts = {
        "PASS": 0,
        "WARN": 0,
        "FAIL": 0
    }
    
    # Add findings from output itself (e.g. from LLM or auto-attach)
    if output.validation_findings:
        all_findings.extend(output.validation_findings)

    for finding in all_findings:
        # Normalize severity to uppercase
        sev = finding.severity.upper()
        if sev in severity_counts:
            severity_counts[sev] += 1
        elif sev == "ERROR":
            severity_counts["FAIL"] += 1
            
    # Determine overall status
    if severity_counts["FAIL"] > 0:
        overall_status = "FAIL"
    elif severity_counts["WARN"] > 0:
        overall_status = "WARN"
    else:
        overall_status = "PASS"
    
    report = {
        "overall_status": overall_status,
        "severity_counts": severity_counts,
        "findings": [f.model_dump() for f in all_findings],
        "total_checks": len(all_findings)
    }
    
    return report
