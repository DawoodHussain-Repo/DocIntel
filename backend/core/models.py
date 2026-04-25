"""Pydantic models for API request and response contracts."""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class UploadContractData(BaseModel):
    """Upload result payload for a successfully indexed contract."""

    file: str = Field(..., min_length=1)
    chunks_indexed: int = Field(..., ge=0)
    collection: str = Field(..., min_length=1)


class HealthData(BaseModel):
    """Health status payload for backend monitoring."""

    service: str
    version: str


class StreamDoneData(BaseModel):
    """Final SSE completion payload."""

    finish_reason: Literal["stop", "error", "timeout"]
    error: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success envelope for all non-streaming endpoints."""

    status: Literal["success"] = "success"
    data: Any
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error envelope for all API failures."""

    status: Literal["error"] = "error"
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None


class AnalyzeDocumentRequest(BaseModel):
    """Request payload for document analysis."""

    file: str = Field(..., min_length=1, max_length=255)


class EvidenceSnippet(BaseModel):
    """A short evidence snippet used to ground analysis outputs."""

    page_number: int = Field(1, ge=1)
    heading: str = Field("Document Section", min_length=1, max_length=200)
    snippet: str = Field(..., min_length=1, max_length=1200)


class DocumentChunk(BaseModel):
    """A retrieved indexed chunk for a single document."""

    source_file: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    page_number: int = Field(1, ge=1)
    heading: str = Field("Document Section", min_length=1, max_length=200)
    chunk_index: int = Field(0, ge=0)
    distance: Optional[float] = None


class ContractClassification(BaseModel):
    """Contract type classification result."""

    contract_type: Literal["NDA", "Lease", "Freelance Agreement", "Other"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., min_length=1, max_length=1200)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)


class ExtractedFieldValue(BaseModel):
    """A single extracted contract field."""

    key: str = Field(..., min_length=1, max_length=64)
    label: str = Field(..., min_length=1, max_length=64)
    value: Optional[str] = Field(default=None, max_length=2000)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)
    notes: Optional[str] = Field(default=None, max_length=1200)


class RiskFlag(BaseModel):
    """A detected risk flag with evidence."""

    title: str = Field(..., min_length=1, max_length=120)
    severity: Literal["low", "medium", "high"]
    score_impact: int = Field(0, ge=-100, le=100)
    description: str = Field(..., min_length=1, max_length=2000)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)


class RiskReport(BaseModel):
    """Overall risk report for the uploaded contract."""

    overall_score: int = Field(..., ge=0, le=100)
    level: Literal["green", "yellow", "red"]
    rationale: str = Field(..., min_length=1, max_length=2000)
    red_flags: List[RiskFlag] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class MissingClause(BaseModel):
    """A checklist item indicating whether a protection is present."""

    name: str = Field(..., min_length=1, max_length=120)
    present: bool
    notes: Optional[str] = Field(default=None, max_length=1200)
    evidence: List[EvidenceSnippet] = Field(default_factory=list)


class ClauseNode(BaseModel):
    """Hierarchical clause node for the parsed contract AST."""

    id: str = Field(..., min_length=1, max_length=64)
    number: Optional[str] = Field(default=None, max_length=32)
    title: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=1, max_length=12000)
    page_start: int = Field(1, ge=1)
    page_end: int = Field(1, ge=1)
    risk_level: Literal["green", "yellow", "red"] = "green"
    children: List["ClauseNode"] = Field(default_factory=list)


class ExecutiveSummaryPayload(BaseModel):
    """Structured model response for executive summary generation."""

    bullets: List[str] = Field(..., min_length=3, max_length=5)


class ExtractedFieldsPayload(BaseModel):
    """Structured model response for field extraction."""

    fields: List[ExtractedFieldValue] = Field(default_factory=list)


class MissingClausesPayload(BaseModel):
    """Structured model response for missing protection detection."""

    missing_clauses: List[MissingClause] = Field(default_factory=list)


class DocumentAnalysisData(BaseModel):
    """Full analysis payload for a single uploaded document."""

    file: str = Field(..., min_length=1)
    executive_summary: List[str] = Field(..., min_length=3, max_length=5)
    classification: ContractClassification
    extracted_fields: List[ExtractedFieldValue] = Field(default_factory=list)
    risk: RiskReport
    missing_clauses: List[MissingClause] = Field(default_factory=list)
    clauses: List[ClauseNode] = Field(default_factory=list)


class UnifiedDocumentAnalysis(BaseModel):
    """
    Single comprehensive analysis output from one LLM call.
    Combines summary, classification, extraction, risk, and missing clauses.
    """
    
    # Executive Summary
    executive_summary: List[str] = Field(
        ..., 
        min_length=3, 
        max_length=5,
        description="3-5 bullet points summarizing key contract terms"
    )
    
    # Classification
    contract_type: Literal["NDA", "Lease", "Freelance Agreement", "Other"] = Field(
        ...,
        description="Primary contract type classification"
    )
    classification_confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence in contract type classification"
    )
    classification_rationale: str = Field(
        ..., 
        min_length=1, 
        max_length=1200,
        description="Brief explanation of classification reasoning"
    )
    
    # Extracted Fields - now with confidence scores
    parties: Optional[str] = Field(default=None, max_length=2000)
    parties_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    effective_date: Optional[str] = Field(default=None, max_length=2000)
    effective_date_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    term: Optional[str] = Field(default=None, max_length=2000)
    term_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    renewal: Optional[str] = Field(default=None, max_length=2000)
    renewal_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    termination_for_convenience: Optional[str] = Field(default=None, max_length=2000)
    termination_for_convenience_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    termination_for_cause: Optional[str] = Field(default=None, max_length=2000)
    termination_for_cause_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    notice_period: Optional[str] = Field(default=None, max_length=2000)
    notice_period_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    payment_amount: Optional[str] = Field(default=None, max_length=2000)
    payment_amount_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    payment_schedule: Optional[str] = Field(default=None, max_length=2000)
    payment_schedule_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    late_fees: Optional[str] = Field(default=None, max_length=2000)
    late_fees_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    currency: Optional[str] = Field(default=None, max_length=2000)
    currency_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    governing_law: Optional[str] = Field(default=None, max_length=2000)
    governing_law_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    jurisdiction: Optional[str] = Field(default=None, max_length=2000)
    jurisdiction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    arbitration: Optional[str] = Field(default=None, max_length=2000)
    arbitration_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    confidentiality: Optional[str] = Field(default=None, max_length=2000)
    confidentiality_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    non_disparagement: Optional[str] = Field(default=None, max_length=2000)
    non_disparagement_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    non_compete: Optional[str] = Field(default=None, max_length=2000)
    non_compete_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    ip_ownership: Optional[str] = Field(default=None, max_length=2000)
    ip_ownership_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    license_grant: Optional[str] = Field(default=None, max_length=2000)
    license_grant_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    assignment: Optional[str] = Field(default=None, max_length=2000)
    assignment_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    subcontracting: Optional[str] = Field(default=None, max_length=2000)
    subcontracting_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    indemnification: Optional[str] = Field(default=None, max_length=2000)
    indemnification_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    limitation_of_liability: Optional[str] = Field(default=None, max_length=2000)
    limitation_of_liability_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    warranties: Optional[str] = Field(default=None, max_length=2000)
    warranties_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    insurance: Optional[str] = Field(default=None, max_length=2000)
    insurance_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    force_majeure: Optional[str] = Field(default=None, max_length=2000)
    force_majeure_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    data_protection: Optional[str] = Field(default=None, max_length=2000)
    data_protection_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    audit_rights: Optional[str] = Field(default=None, max_length=2000)
    audit_rights_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    change_control: Optional[str] = Field(default=None, max_length=2000)
    change_control_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    signature_block: Optional[str] = Field(default=None, max_length=2000)
    signature_block_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Risk Assessment
    risk_overall_score: int = Field(..., ge=0, le=100, description="Overall risk score 0-100")
    risk_level: Literal["green", "yellow", "red"] = Field(..., description="Risk level indicator")
    risk_rationale: str = Field(..., min_length=1, max_length=2000, description="Risk assessment reasoning")
    risk_red_flags: List[RiskFlag] = Field(default_factory=list, description="Identified risk factors")
    risk_recommendations: List[str] = Field(default_factory=list, max_length=10, description="Risk mitigation recommendations")
    
    # Missing Clauses
    missing_clauses: List[MissingClause] = Field(
        default_factory=list,
        description="Checklist of expected protections and their presence"
    )


class RewriteClauseRequest(BaseModel):
    """Request payload for generating a rewritten clause."""

    file: str = Field(..., min_length=1, max_length=255)
    clause_text: str = Field(..., min_length=1, max_length=12000)
    goal: Optional[str] = Field(default=None, max_length=2000)


class RewriteClauseData(BaseModel):
    """Response payload for a rewritten clause proposal."""

    replacement_clause: str = Field(..., min_length=1, max_length=12000)
    rationale: str = Field(..., min_length=1, max_length=4000)
    negotiation_notes: List[str] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)


ClauseNode.model_rebuild()
