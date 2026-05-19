"""Document analysis service: unified single-request comprehensive analysis."""

from __future__ import annotations

import asyncio
import json
from typing import Any, List

import structlog
from langchain_openai import ChatOpenAI

from core.analysis_catalog import FIELD_SPECS
from core.clause_parser import build_clause_ast
from core.llm_utils import invoke_structured_model
from core.prompts import (
    UNIFIED_ANALYSIS_SYSTEM_PROMPT,
    build_unified_analysis_prompt,
)
from core.retrieval import (
    ensure_document_exists,
    retrieve_comprehensive_evidence,
    retrieve_document_chunks,
)
from core.models import (
    ContractClassification,
    DocumentAnalysisData,
    ExtractedFieldValue,
    RiskReport,
    UnifiedDocumentAnalysis,
)


logger = structlog.get_logger("docintel.analysis_service")


def _truncate(text: str, max_chars: int = 400) -> str:
    """Truncate text to max_chars while preserving semantic meaning."""
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    # Try to break at sentence boundary
    truncated = text[:max_chars]
    last_period = truncated.rfind('. ')
    if last_period > max_chars * 0.7:  # If we can break at a sentence within 70% of limit
        return truncated[:last_period + 1]
    return truncated[:max_chars - 3] + "..."


def _evidence_payload(excerpts: List[dict[str, Any]]) -> List[dict[str, Any]]:
    """Format evidence excerpts for LLM consumption."""
    return [
        {
            "page_number": excerpt.get("page_number"),
            "heading": excerpt.get("heading"),
            "snippet": _truncate(str(excerpt.get("text", ""))),
        }
        for excerpt in excerpts
    ]


async def _build_extracted_fields(
    unified: UnifiedDocumentAnalysis,
    source_file: str,
    chroma_client: Any,
) -> List[ExtractedFieldValue]:
    """Retrieve supporting evidence concurrently for extracted fields."""
    from core.models import EvidenceSnippet
    from core.retrieval import retrieve_chunks

    field_mapping = {spec[0]: (spec[1], spec[2]) for spec in FIELD_SPECS}
    active_fields = [
        (
            field_key,
            field_label,
            field_query,
            value,
            getattr(unified, f"{field_key}_confidence", 0.0),
        )
        for field_key, (field_label, field_query) in field_mapping.items()
        if (value := getattr(unified, field_key, None)) is not None
    ]

    if not active_fields:
        return []

    evidence_results = await asyncio.gather(
        *[
            asyncio.to_thread(
                retrieve_chunks,
                chroma_client,
                field_query,
                source_file,
                2,
            )
            for _, _, field_query, _, _ in active_fields
        ]
    )

    extracted_fields: List[ExtractedFieldValue] = []
    for (field_key, field_label, _field_query, value, confidence), evidence_chunks in zip(
        active_fields,
        evidence_results,
    ):
        evidence_snippets = [
            EvidenceSnippet(
                page_number=chunk.get("page_number", 1),
                heading=chunk.get("heading", "Document Section"),
                snippet=_truncate(chunk.get("text", ""), max_chars=400),
            )
            for chunk in evidence_chunks
        ]
        extracted_fields.append(
            ExtractedFieldValue(
                key=field_key,
                label=field_label,
                value=value,
                confidence=confidence,
                evidence=evidence_snippets,
                notes=None,
            )
        )

    return extracted_fields


async def _convert_unified_to_legacy_format(
    unified: UnifiedDocumentAnalysis,
    source_file: str,
    chroma_client: Any,
) -> DocumentAnalysisData:
    """
    Convert unified analysis output to legacy DocumentAnalysisData format.
    Retrieves evidence snippets for each extracted field to maintain quality.
    This maintains backward compatibility with existing API contracts.
    """
    # Build classification
    classification = ContractClassification(
        contract_type=unified.contract_type,
        confidence=unified.classification_confidence,
        rationale=unified.classification_rationale,
        evidence=[],
    )
    extracted_fields = await _build_extracted_fields(
        unified,
        source_file,
        chroma_client,
    )
    
    # Build risk report
    risk = RiskReport(
        overall_score=unified.risk_overall_score,
        level=unified.risk_level,
        rationale=unified.risk_rationale,
        red_flags=unified.risk_red_flags,
        recommendations=unified.risk_recommendations,
    )
    
    return DocumentAnalysisData(
        file=source_file,
        executive_summary=unified.executive_summary,
        classification=classification,
        extracted_fields=extracted_fields,
        risk=risk,
        missing_clauses=unified.missing_clauses,
        clauses=[],  # Will be populated separately
    )


async def analyze_document(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
) -> DocumentAnalysisData:
    """
    Perform comprehensive document analysis in a SINGLE LLM request.
    
    This is the new unified architecture that replaces 10 sequential requests
    with 1 comprehensive request, reducing latency from ~30s to ~8s.
    
    Args:
        llm: Configured LLM instance
        chroma_client: ChromaDB client
        source_file: Document filename to analyze
    
    Returns:
        Complete document analysis
    """
    await asyncio.to_thread(ensure_document_exists, chroma_client, source_file)
    
    logger.info("unified_analysis_started", file=source_file)
    
    # Step 1: Retrieve comprehensive evidence (20 diverse chunks)
    evidence_chunks = await asyncio.to_thread(
        retrieve_comprehensive_evidence,
        chroma_client,
        source_file,
        max_chunks=20,
    )
    
    evidence_json = json.dumps(
        _evidence_payload(evidence_chunks),
        ensure_ascii=False,
        indent=2,
    )
    
    logger.info(
        "evidence_retrieved",
        file=source_file,
        chunks=len(evidence_chunks),
        estimated_tokens=len(evidence_json) // 4,
    )
    
    # Step 2: Single comprehensive LLM call
    unified_result = await invoke_structured_model(
        llm,
        UnifiedDocumentAnalysis,
        UNIFIED_ANALYSIS_SYSTEM_PROMPT,
        build_unified_analysis_prompt(evidence_json),
        chain_name="unified_analysis",
    )
    
    logger.info(
        "unified_analysis_completed",
        file=source_file,
        contract_type=unified_result.contract_type,
        risk_score=unified_result.risk_overall_score,
        fields_extracted=sum(1 for field in FIELD_SPECS if getattr(unified_result, field[0], None)),
    )
    
    # Step 3: Convert analysis payload and fetch document chunks in parallel
    analysis_task = _convert_unified_to_legacy_format(
        unified_result,
        source_file,
        chroma_client,
    )
    document_chunks_task = asyncio.to_thread(
        retrieve_document_chunks,
        chroma_client,
        source_file,
    )
    analysis, document_chunks = await asyncio.gather(
        analysis_task,
        document_chunks_task,
    )

    # Step 4: Build clause AST (separate step, not LLM-based)
    analysis.clauses = await asyncio.to_thread(
        build_clause_ast,
        document_chunks,
        analysis.risk,
    )
    
    logger.info(
        "analysis_completed",
        file=source_file,
        contract_type=analysis.classification.contract_type,
        clause_count=len(analysis.clauses),
        total_requests=1,  # Down from 10!
    )
    
    return analysis
