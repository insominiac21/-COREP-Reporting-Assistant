"""Common pydantic models for COREP Assistant"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk"""
    chunk_id: str
    template_id: str  # C01.00, C07.00, or UNKNOWN
    chunk_type: str  # template_overview, row_definition, column_definition, validation_rule, q_and_a
    row_code: Optional[str] = None
    col_code: Optional[str] = None
    legal_refs: List[str] = Field(default_factory=list)
    source_doc: str
    page_start: int
    page_end: int
    section_path: Optional[str] = None


class Chunk(BaseModel):
    """A document chunk with text and metadata"""
    text: str
    metadata: ChunkMetadata


class EvidenceChunk(BaseModel):
    """Evidence chunk returned from retrieval"""
    chunk_id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class AnswerItem(BaseModel):
    """A single populated template cell/row"""
    row_code: str
    col_code: str = "0010"  # default to amount column
    concept: str = "unknown"
    value: Optional[float] = None
    unit: str = "GBP"
    confidence: float = 0.5
    evidence: List[Dict[str, str]] = Field(default_factory=list)  # [{chunk_id, quote_span}]
    reasoning: str = ""


class MissingInput(BaseModel):
    """Documentation of missing information"""
    field: str
    why_needed: str


class ValidationFinding(BaseModel):
    """A validation check result"""
    severity: str = "WARN"  # PASS, WARN, FAIL
    rule_id: str = "UNKNOWN"
    message: str = "Validation finding"
    impacted_cells: List[str] = Field(default_factory=list)



class AnswerCitation(BaseModel):
    """Citation for natural language answer"""
    chunk_id: str
    quote_span: str
    purpose: str = "general"


class ScenarioFeatures(BaseModel):
    """Features extracted from user scenario"""
    is_default: bool = False
    suggested_risk_weight: Optional[float] = None
    is_off_balance: bool = False
    # Extracted amounts
    mortgage_amount_gbp: Optional[float] = None
    exposure_amount_gbp: Optional[float] = None
    nominal_amount_gbp: Optional[float] = None


class TemplateOutput(BaseModel):
    """Structured output for a template"""
    template_id: str
    jurisdiction: str = "UK"
    version_tag: str = "2024-09"
    as_of_date: str
    answers: List[AnswerItem] = Field(default_factory=list)
    final_answer: str = ""
    answer_citations: List[AnswerCitation] = Field(default_factory=list)
    missing_inputs: List[MissingInput] = Field(default_factory=list)
    validation_findings: List[ValidationFinding] = Field(default_factory=list)
    audit_log: List[Dict[str, Any]] = Field(default_factory=list)


class RetrievalRequest(BaseModel):
    """Request for hybrid retrieval"""
    query: str
    template_id: str
    top_k: int = 6
    use_bm25: bool = True
    use_faiss: bool = True


class AskRequest(BaseModel):
    """User question request"""
    template_id: str
    as_of_date: str
    scenario: str
    question: str
    top_k: int = 6
    use_bm25: bool = True
    use_faiss: bool = True
    citation_strict: bool = True
    confidence_threshold: float = 0.65


class AskResponse(BaseModel):
    """Response to user question"""
    request_id: str
    template_id: str
    evidence: List[EvidenceChunk]
    structured_output: TemplateOutput
    rendered_template_html: str
    validation: Dict[str, Any]
    timestamp: Optional[datetime] = None

