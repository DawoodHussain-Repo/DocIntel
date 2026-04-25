"""Document analysis service: summary, classification, extraction, risk, and clause parsing."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import structlog
from langchain_openai import ChatOpenAI

from core.analysis_catalog import (
    CLASSIFICATION_QUERIES,
    FIELD_SPECS,
    PLAYBOOK,
    RISK_QUERIES,
    SUMMARY_QUERIES,
)
from core.clause_parser import build_clause_ast
from core.llm_utils import invoke_structured_model
from core.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    EXTRACTION_SYSTEM_PROMPT,
    MISSING_CLAUSE_SYSTEM_PROMPT,
    RISK_SYSTEM_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    build_classification_prompt,
    build_extraction_prompt,
    build_missing_clause_prompt,
    build_risk_prompt,
    build_summary_prompt,
)
from core.retrieval import (
    ensure_document_exists,
    retrieve_chunks,
    retrieve_document_chunks,
    retrieve_for_queries,
)
from core.models import (
    ContractClassification,
    DocumentAnalysisData,
    ExecutiveSummaryPayload,
    ExtractedFieldValue,
    ExtractedFieldsPayload,
    MissingClause,
    MissingClausesPayload,
    RiskReport,
)


logger = structlog.get_logger("docintel.analysis_service")


def _truncate(text: str, max_chars: int = 900) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def _evidence_payload(excerpts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "page_number": excerpt.get("page_number"),
            "heading": excerpt.get("heading"),
            "snippet": _truncate(str(excerpt.get("text", ""))),
        }
        for excerpt in excerpts
    ]


async def generate_executive_summary(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
) -> List[str]:
    excerpts = retrieve_for_queries(
        chroma_client,
        SUMMARY_QUERIES,
        source_file,
        n_results_each=3,
        max_total=18,
    )
    payload = await invoke_structured_model(
        llm,
        ExecutiveSummaryPayload,
        SUMMARY_SYSTEM_PROMPT,
        build_summary_prompt(json.dumps(_evidence_payload(excerpts), ensure_ascii=False)),
        chain_name="analysis_summary",
    )
    return [bullet.strip("- \n\r\t") for bullet in payload.bullets if bullet.strip()][:5]


async def classify_contract(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
) -> ContractClassification:
    excerpts = retrieve_for_queries(
        chroma_client,
        CLASSIFICATION_QUERIES,
        source_file,
        n_results_each=3,
        max_total=12,
    )
    return await invoke_structured_model(
        llm,
        ContractClassification,
        CLASSIFICATION_SYSTEM_PROMPT,
        build_classification_prompt(json.dumps(_evidence_payload(excerpts), ensure_ascii=False)),
        chain_name="analysis_classification",
    )


async def extract_fields(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
) -> List[ExtractedFieldValue]:
    evidence_by_field = [
        {
            "key": key,
            "label": label,
            "evidence": _evidence_payload(
                retrieve_chunks(chroma_client, query, source_file, n_results=2)
            ),
        }
        for key, label, query in FIELD_SPECS
    ]
    payload = await invoke_structured_model(
        llm,
        ExtractedFieldsPayload,
        EXTRACTION_SYSTEM_PROMPT,
        build_extraction_prompt(json.dumps(evidence_by_field, ensure_ascii=False)),
        chain_name="analysis_extraction",
    )
    return payload.fields


async def scan_risk(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
    classification: ContractClassification,
    extracted_fields: List[ExtractedFieldValue],
) -> RiskReport:
    excerpts = retrieve_for_queries(
        chroma_client,
        RISK_QUERIES,
        source_file,
        n_results_each=3,
        max_total=14,
    )
    return await invoke_structured_model(
        llm,
        RiskReport,
        RISK_SYSTEM_PROMPT,
        build_risk_prompt(
            classification.contract_type,
            json.dumps([field.model_dump() for field in extracted_fields], ensure_ascii=False),
            json.dumps(_evidence_payload(excerpts), ensure_ascii=False),
        ),
        chain_name="analysis_risk",
    )


async def detect_missing_clauses(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
    classification: ContractClassification,
) -> List[MissingClause]:
    clause_checks = PLAYBOOK.get(classification.contract_type, PLAYBOOK["Other"])
    payload = [
        {
            "name": name,
            "query": query,
            "excerpts": _evidence_payload(
                retrieve_chunks(chroma_client, query, source_file, n_results=2)
            ),
        }
        for name, query in clause_checks
    ]
    result = await invoke_structured_model(
        llm,
        MissingClausesPayload,
        MISSING_CLAUSE_SYSTEM_PROMPT,
        build_missing_clause_prompt(json.dumps(payload, ensure_ascii=False)),
        chain_name="analysis_missing_clauses",
    )
    return result.missing_clauses


async def analyze_document(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
) -> DocumentAnalysisData:
    ensure_document_exists(chroma_client, source_file)
    document_chunks = retrieve_document_chunks(chroma_client, source_file)

    logger.info("analysis_started", file=source_file)
    summary = await generate_executive_summary(llm, chroma_client, source_file)
    classification = await classify_contract(llm, chroma_client, source_file)
    extracted_fields = await extract_fields(llm, chroma_client, source_file)
    risk = await scan_risk(llm, chroma_client, source_file, classification, extracted_fields)
    missing_clauses = await detect_missing_clauses(llm, chroma_client, source_file, classification)
    clauses = build_clause_ast(document_chunks, risk)
    logger.info(
        "analysis_completed",
        file=source_file,
        contract_type=classification.contract_type,
        clause_count=len(clauses),
    )

    return DocumentAnalysisData(
        file=source_file,
        executive_summary=summary,
        classification=classification,
        extracted_fields=extracted_fields,
        risk=risk,
        missing_clauses=missing_clauses,
        clauses=clauses,
    )
