"""Clause and section parsing helpers for contract AST output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from hashlib import sha1
from typing import Iterable, List

from core.models import ClauseNode, DocumentChunk, RiskReport


DEFAULT_HEADING = "Document Section"
HEADING_NUMBER_PATTERN = re.compile(
    r"^(?:section|clause)?\s*(?P<number>\d+(?:\.\d+)*)[\)\].:\- ]*(?P<title>.+)?$",
    re.IGNORECASE,
)
SUBCLAUSE_PATTERN = re.compile(
    r"^\s*(?P<number>(?:\d+\.\d+)|(?:\([a-z0-9ivxlcdm]+\))|(?:[a-z0-9ivxlcdm]+[\).]))\s+(?P<body>.+)$",
    re.IGNORECASE,
)


@dataclass
class DocumentSection:
    """Ordered section reconstructed from indexed chunks."""

    key: str
    heading: str
    page_start: int
    page_end: int
    chunks: List[DocumentChunk] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(chunk.text.strip() for chunk in self.chunks if chunk.text.strip())


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().lower()


def _derive_title_from_text(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return DEFAULT_HEADING
    return first_line[:96]


def _section_key(chunk: DocumentChunk) -> str:
    normalized_heading = _normalize_text(chunk.heading)
    if not normalized_heading or normalized_heading == _normalize_text(DEFAULT_HEADING):
        return f"chunk:{chunk.chunk_index}"
    return f"heading:{normalized_heading}"


def group_document_sections(chunks: Iterable[DocumentChunk]) -> List[DocumentSection]:
    """Collapse ordered document chunks into top-level sections."""
    sections: List[DocumentSection] = []
    current: DocumentSection | None = None

    for chunk in sorted(chunks, key=lambda item: item.chunk_index):
        section_key = _section_key(chunk)
        if current is None or current.key != section_key:
            current = DocumentSection(
                key=section_key,
                heading=chunk.heading or DEFAULT_HEADING,
                page_start=chunk.page_number,
                page_end=chunk.page_number,
                chunks=[chunk],
            )
            sections.append(current)
            continue

        current.chunks.append(chunk)
        current.page_end = max(current.page_end, chunk.page_number)

    return sections


def _parse_heading(heading: str, fallback_text: str) -> tuple[str | None, str]:
    normalized_heading = (heading or "").strip()
    if not normalized_heading or normalized_heading == DEFAULT_HEADING:
        return None, _derive_title_from_text(fallback_text)

    match = HEADING_NUMBER_PATTERN.match(normalized_heading)
    if not match:
        return None, normalized_heading

    number = match.group("number")
    title = (match.group("title") or "").strip()
    return number, title or normalized_heading


def _make_clause_id(prefix: str, number: str | None, title: str, page_start: int) -> str:
    digest = sha1(f"{prefix}|{number or ''}|{title}|{page_start}".encode("utf-8")).hexdigest()
    return digest[:16]


def _extract_subclauses(
    parent_id: str,
    parent_text: str,
    page_start: int,
    page_end: int,
    risk_level: str,
) -> List[ClauseNode]:
    lines = [line.rstrip() for line in parent_text.splitlines() if line.strip()]
    matches = [(index, SUBCLAUSE_PATTERN.match(line)) for index, line in enumerate(lines)]
    candidate_indexes = [index for index, match in matches if match]
    if len(candidate_indexes) < 2:
        return []

    children: List[ClauseNode] = []
    for offset, line_index in enumerate(candidate_indexes):
        match = SUBCLAUSE_PATTERN.match(lines[line_index])
        if match is None:
            continue

        block_end = candidate_indexes[offset + 1] if offset + 1 < len(candidate_indexes) else len(lines)
        block_lines = lines[line_index:block_end]
        text = "\n".join(block_lines).strip()
        number = match.group("number").strip("()")
        title = match.group("body").strip()[:96]
        children.append(
            ClauseNode(
                id=_make_clause_id(parent_id, number, title, page_start),
                number=number,
                title=title,
                text=text,
                page_start=page_start,
                page_end=page_end,
                risk_level=risk_level,
                children=[],
            )
        )

    return children


def _evidence_matches_clause(clause: ClauseNode, risk: RiskReport) -> str:
    severity_order = {"green": 0, "yellow": 1, "red": 2}
    severity_map = {"low": "green", "medium": "yellow", "high": "red"}
    current_level = clause.risk_level
    clause_text = _normalize_text(clause.text)
    clause_title = _normalize_text(clause.title)

    for flag in risk.red_flags:
        next_level = severity_map.get(flag.severity, "green")
        for evidence in flag.evidence:
            heading = _normalize_text(evidence.heading)
            snippet = _normalize_text(evidence.snippet)
            heading_match = bool(heading and (heading in clause_title or clause_title in heading))
            snippet_match = bool(snippet and snippet[:160] in clause_text)

            if heading_match or snippet_match:
                if severity_order[next_level] > severity_order[current_level]:
                    current_level = next_level

    return current_level


def build_clause_ast(chunks: Iterable[DocumentChunk], risk: RiskReport) -> List[ClauseNode]:
    """Build a clause tree from ordered chunks and annotate it with risk levels."""
    clauses: List[ClauseNode] = []

    for section in group_document_sections(chunks):
        text = section.text
        if not text:
            continue

        number, title = _parse_heading(section.heading, text)
        clause_id = _make_clause_id(section.key, number, title, section.page_start)
        clause = ClauseNode(
            id=clause_id,
            number=number,
            title=title,
            text=text,
            page_start=section.page_start,
            page_end=section.page_end,
            risk_level="green",
            children=[],
        )
        clause.risk_level = _evidence_matches_clause(clause, risk)
        clause.children = _extract_subclauses(
            parent_id=clause.id,
            parent_text=text,
            page_start=clause.page_start,
            page_end=clause.page_end,
            risk_level=clause.risk_level,
        )
        clauses.append(clause)

    return clauses
