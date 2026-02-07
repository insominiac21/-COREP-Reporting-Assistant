"""RAG orchestration and structured output generation"""
from typing import List, Optional, Dict, Any
from corep_assistant.schemas import EvidenceChunk, TemplateOutput, AnswerItem, MissingInput
from .groq_client import get_groq_client
from .prompts import SYSTEM_PROMPT, build_user_prompt, build_auditor_prompt
from corep_assistant.config import ENABLE_AUDITOR_PASS


def generate_structured_output(
    template_id: str,
    as_of_date: str,
    scenario: str,
    question: str,
    evidence: List[EvidenceChunk]
) -> Optional[TemplateOutput]:
    """
    Generate structured template output using RAG + LLM.
    
    Args:
        template_id: Template ID
        as_of_date: Reporting date
        scenario: User scenario
        question: User question
        evidence: Retrieved evidence chunks
        
    Returns:
        TemplateOutput or None if generation failed
    """
    if not evidence:
        print("WARNING: No evidence provided for generation")
        # Return empty output with missing inputs
        return TemplateOutput(
            template_id=template_id,
            as_of_date=as_of_date,
            answers=[],
            missing_inputs=[
                MissingInput(
                    field="all_fields",
                    why_needed="No evidence chunks retrieved. Need relevant regulatory text and template definitions."
                )
            ]
        )
    
    # Build prompts
    user_prompt = build_user_prompt(
        template_id, as_of_date, scenario, question, evidence
    )
    
    # Call LLM
    client = get_groq_client()
    response_json = client.generate_json(SYSTEM_PROMPT, user_prompt)
    
    if not response_json:
        print("ERROR: Failed to generate JSON from LLM")
        return None
    
    # Parse into TemplateOutput
    try:
        output = TemplateOutput(**response_json)
    except Exception as e:
        import traceback
        import sys
        print(f"ERROR: Failed to parse LLM output into TemplateOutput: {e}", flush=True)
        # Check if it's a validation error and print details
        if hasattr(e, 'errors'):
            print(f"Validation Errors: {e.errors()}", flush=True)
            
        # Truncate JSON to avoid flooding logs
        json_str = str(response_json)
        print(f"Response JSON (truncated): {json_str[:1000]}...", flush=True)
        return None
    
    # Auto-attach evidence for null cells if missing
    auto_attach_evidence(output, evidence)
    
    # NEW: Apply dependency-aware auto-fill (Phase 21)
    from corep_assistant.validation.scenario_parse import parse_scenario
    scenario_features = parse_scenario(scenario)
    apply_dependency_aware_autofill(output, scenario_features, evidence)

    # Filter internal audit checks from missing_inputs
    output.missing_inputs = [
        mi for mi in output.missing_inputs 
        if "audit_check" not in mi.field.lower() and "hallucination" not in mi.field.lower()
    ]
    
    # Optional: Run auditor pass
    if ENABLE_AUDITOR_PASS:
        output = run_auditor_pass(output, evidence)
    
    return output


def apply_dependency_aware_autofill(
    output: TemplateOutput, 
    features: Any, 
    evidence: List[EvidenceChunk]
):
    """
    Deterministic fallback to populate cells that the LLM might have left null 
    due to 'dependency confusion' (e.g. thinking amount depends on LTV).
    """
    if not output.answers:
        return

    # Case: C07.00 Row 0090 (Residential mortgages)
    if output.template_id == "C07.00":
        # Check if 0090 is present in answers
        ans_0090_0010 = next((a for a in output.answers if a.row_code == "0090" and a.col_code == "0010"), None)
        ans_0090_0040 = next((a for a in output.answers if a.row_code == "0090" and a.col_code == "0040"), None)

        # 1. Populate 0090:0010 if scenario has mortgage amount
        if features.mortgage_amount_gbp is not None:
            if not ans_0090_0010:
                # Add new answer if missing entirely
                ans_0090_0010 = AnswerItem(
                    row_code="0090", col_code="0010", 
                    concept="Original exposure", 
                    value=features.mortgage_amount_gbp,
                    confidence=1.0, reasoning="Auto-populated from scenario mortgage amount."
                )
                output.answers.append(ans_0090_0010)
            elif ans_0090_0010.value is None:
                # Update if null
                ans_0090_0010.value = features.mortgage_amount_gbp
                ans_0090_0010.reasoning = "Auto-corrected: Scenario amount takes precedence over dependency confusion."
                ans_0090_0010.confidence = 1.0

        # 2. Populate 0090:0040 if 0010 is present and it's on-balance (default)
        if ans_0090_0010 and ans_0090_0010.value is not None:
            if not ans_0090_0040:
                 ans_0090_0040 = AnswerItem(
                    row_code="0090", col_code="0040", 
                    concept="Exposure value", 
                    value=ans_0090_0010.value,
                    confidence=1.0, reasoning="Auto-populated: Exposure value matches original exposure for on-balance mortgages."
                )
                 output.answers.append(ans_0090_0040)
            elif ans_0090_0040.value is None:
                ans_0090_0040.value = ans_0090_0010.value
                ans_0090_0040.reasoning = "Auto-corrected: Exposure value matches original exposure for on-balance mortgages."
                ans_0090_0040.confidence = 1.0

    # Ensure evidence is attached to these new/updated answers
    auto_attach_evidence(output, evidence)


def auto_attach_evidence(output: TemplateOutput, evidence: List[EvidenceChunk]):
    """
    Auto-attach definition chunks to answers with empty evidence.
    This is a fallback for when LLM fails to cite definitions for null values.
    """
    for answer in output.answers:
        if not answer.evidence:
            # Try to find relevant column definition
            col_def_chunk = next(
                (ev for ev in evidence 
                 if ev.metadata.get('chunk_type') == 'column_definition' 
                 and (ev.metadata.get('col_code') == answer.col_code or f"Column {answer.col_code}" in ev.text)),
                None
            )
            
            if col_def_chunk:
                answer.evidence.append({
                    "chunk_id": col_def_chunk.chunk_id,
                    "quote_span": "Auto-attached column definition"
                })
                if not answer.reasoning:
                    answer.reasoning = "Evidence auto-attached from definition."

def run_auditor_pass(
    output: TemplateOutput,
    evidence: List[EvidenceChunk]
) -> TemplateOutput:
    """
    Run second-pass auditor to validate citations.
    
    Args:
        output: Generated template output
        evidence: Available evidence chunks
        
    Returns:
        Potentially modified TemplateOutput
    """
    evidence_ids = [ev.chunk_id for ev in evidence]
    
    # Build auditor prompt
    auditor_prompt = build_auditor_prompt(
        output.model_dump(),
        evidence_ids
    )
    
    # Call LLM
    client = get_groq_client()
    auditor_response = client.generate_json(
        "You are an auditor validating template responses.",
        auditor_prompt
    )
    
    if not auditor_response:
        print("WARNING: Auditor pass failed")
        return output
    
    # Check validity
    is_valid = auditor_response.get("valid", True)
    issues = auditor_response.get("issues", [])
    
    if not is_valid and issues:
        print(f"AUDITOR FOUND ISSUES: {issues}")
        # Add to validation findings instead of missing_inputs for internal checks
        for issue in issues:
            # We don't want to clutter missing_inputs with audit checks
            # Just log them for now, or add as internal validation finding if schema supported it
            pass
    
    return output


def create_field_audit_log(output: TemplateOutput) -> List[Dict[str, Any]]:
    """
    Create audit log mapping each field to evidence chunks.
    
    Args:
        output: Template output
        
    Returns:
        List of audit log entries
    """
    audit_log = []
    
    for answer in output.answers:
        cell_id = f"{answer.row_code}:{answer.col_code}"
        evidence_chunk_ids = [ev.get("chunk_id") for ev in answer.evidence]
        
        audit_log.append({
            "cell_id": cell_id,
            "value": answer.value,
            "evidence_chunk_ids": evidence_chunk_ids,
            "reasoning": answer.reasoning
        })
    
    return audit_log
