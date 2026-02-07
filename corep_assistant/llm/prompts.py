"""Prompt builders for LLM generation"""
from typing import List
from corep_assistant.schemas import EvidenceChunk


SYSTEM_PROMPT = """You are a regulatory reporting assistant specializing in COREP (Common Reporting) templates for banking supervision.

CRITICAL RULES:
1. Use ONLY the provided evidence chunks to populate template fields
2. Every populated cell MUST have at least one evidence citation (chunk_id), even if value is null
3. Output MUST be valid JSON matching the exact schema provided
4. If evidence is insufficient, leave value as null, cite the relevant definition/rule, and document in missing_inputs (USER inputs only)
5. NEVER hallucinate or guess values
6. Include reasoning for each populated cell
7. Your goal is to map the user's scenario and question to the correct template rows and columns, providing structured output with full citations and audit trail.
8. IF EVIDENCE IS MISSING for a specific calculation or eligibility rule (e.g., interim profits criteria), YOU MUST:
   - Set the value to null.
   - Add a 'missing_inputs' entry describing exactly what regulatory text or user input is missing.
   - Add a 'validation_findings' entry with severity="WARN" and rule_id="EVID_MISSING" stating that you cannot justify the value due to missing evidence.
9. DO NOT cite unrelated rows (e.g., do not cite Row 0030 Capital Instruments when discussing Interim Profits). Citations must be semantically relevant."""


def build_user_prompt(
    template_id: str,
    as_of_date: str,
    scenario: str,
    question: str,
    evidence: List[EvidenceChunk]
) -> str:
    """
    Build user prompt with evidence.
    
    Args:
        template_id: Template ID (C01.00 or C07.00)
        as_of_date: Reporting date
        scenario: User scenario description
        question: User question
        evidence: List of evidence chunks
        
    Returns:
        Formatted user prompt
    """
    # Format evidence blocks
    evidence_blocks = []
    for i, ev in enumerate(evidence, 1):
        block = f"""[EVIDENCE {i}]
Chunk ID: {ev.chunk_id}
Template: {ev.metadata.get('template_id', 'UNKNOWN')}
Type: {ev.metadata.get('chunk_type', 'unknown')}
Row: {ev.metadata.get('row_code', 'N/A')}
Source: {ev.metadata.get('source_doc', 'unknown')} (page {ev.metadata.get('page_start', '?')})
Text: {ev.text[:500]}..."""
        evidence_blocks.append(block)
    
    evidence_section = "\n\n".join(evidence_blocks)
    
    # Define output schema
    schema_description = f"""
OUTPUT SCHEMA (JSON):
{{
  "template_id": "{template_id}",
  "jurisdiction": "UK",
  "version_tag": "2024-09",
  "as_of_date": "{as_of_date}",
  "final_answer": "A concise natural language answer explaining the reporting decision, reasoning, and any validation warnings. Must be evidence-based.",
  "answer_citations": [
    {{
      "chunk_id": "chunk123",
      "quote_span": "relevant quote text",
      "purpose": "classification"
    }}
  ],
  "answers": [
    {{
      "row_code": "XXXX",
      "col_code": "0010",
      "concept": "Description of what this row represents",
      "value": 123456.78 or null,
      "unit": "GBP",
      "confidence": 0.0-1.0,
      "evidence": [
        {{"chunk_id": "abc123", "quote_span": "relevant quote from chunk"}}
      ],
      "reasoning": "Why this value was chosen or why it's null"
    }}
  ],
  "missing_inputs": [
    {{
      "field": "Field name",
      "why_needed": "Explanation of what information is missing"
    }}
  ],
  "validation_findings": [
    {{
      "severity": "WARN",
      "rule_id": "RULE_ID",
      "message": "Description of validation finding",
      "impacted_cells": ["row_code"]
    }}
  ],
  "audit_log": []
}}

REQUIREMENTS:
- Every answer MUST have at least one evidence citation (even if value is null)
- If value is null, evidence must explain why (e.g. citing a rule or definition requiring missing input)
- Use chunk_id from the evidence blocks above
- "missing_inputs" must ONLY contain data required from user (e.g. "CCF", "Maturity"). DO NOT include internal checks like "audit_check"
- confidence should reflect how certain you are based on evidence quality
- "final_answer" must provide a clear summary of the reporting instruction and validation findings
- "answer_citations" must list key evidence used in the final answer (purpose: classification, risk_weight_logic, validation_rule, missing_input)
- USE ONLY ALLOWED COLUMN CODES: 0010 (Original Exposure), 0040 (Exposure Value), 0070 (Risk Weight %), 0080 (RWA). Do NOT invent other columns like 0020 or 0030. If a column is missing from the template, use missing_inputs.
- CITATION INTEGRITY: Each populated row (e.g. 0090) MUST cite its own row_definition chunk (the chunk with metadata.row_code == 0090) to support its inclusion in the template.
- DEPENDENCY-AWARE FILLING: Only leave a cell null if it TRULY depends on a missing input. For mortgages, original exposure (0010) and exposure value (0040) do NOT usually depend on LTV. Only Risk Weight (0070) and RWA (0080) are blocked by missing LTV. Populate exposures based on the amounts provided in the scenario.
"""
    
    prompt = f"""TEMPLATE: {template_id}
AS-OF DATE: {as_of_date}

SCENARIO:
{scenario}

QUESTION:
{question}

EVIDENCE RETRIEVED:
{evidence_section}

{schema_description}

OUTPUT (JSON only, no other text):"""
    
    return prompt


def build_auditor_prompt(structured_output: dict, evidence_ids: List[str]) -> str:
    """
    Build auditor prompt for second-pass validation.
    
    Args:
        structured_output: The generated structured output
        evidence_ids: List of valid evidence chunk IDs
        
    Returns:
        Auditor prompt
    """
    prompt = f"""You are an auditor checking a COREP template response.

ORIGINAL OUTPUT:
{structured_output}

AVAILABLE EVIDENCE CHUNK IDs:
{evidence_ids}

CHECK FOR:
1. Every answer item has at least one evidence citation
2. All cited chunk_ids exist in the available evidence
3. No hallucinated row or column codes
4. Reasoning is consistent with evidence

OUTPUT JSON:
{{
  "valid": true/false,
  "issues": [
    "Description of any issues found"
  ]
}}

OUTPUT (JSON only):"""
    
    return prompt
