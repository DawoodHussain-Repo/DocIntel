"""Clause rewriting service ("Fix This")."""

from __future__ import annotations

import json
from typing import Any, Optional

from langchain_openai import ChatOpenAI

from core.llm_utils import invoke_structured_model
from core.prompts import REWRITE_SYSTEM_PROMPT, build_rewrite_prompt
from core.retrieval import ensure_document_exists, retrieve_for_queries
from core.models import RewriteClauseData


async def rewrite_clause(
    llm: ChatOpenAI,
    chroma_client: Any,
    source_file: str,
    clause_text: str,
    goal: Optional[str] = None,
) -> RewriteClauseData:
    """Generate a grounded clause rewrite using nearby contract context."""
    ensure_document_exists(chroma_client, source_file)

    context_excerpts = retrieve_for_queries(
        chroma_client,
        [
            "parties to this agreement",
            "governing law",
            "payment terms",
            "term and termination",
        ],
        source_file,
        n_results_each=2,
        max_total=6,
    )
    context_payload = [
        {
            "page_number": excerpt.get("page_number"),
            "heading": excerpt.get("heading"),
            "snippet": (
                f"{str(excerpt.get('text', ''))[:700]}..."
                if len(str(excerpt.get("text", ""))) > 700
                else str(excerpt.get("text", ""))
            ),
        }
        for excerpt in context_excerpts
    ]

    return await invoke_structured_model(
        llm,
        RewriteClauseData,
        REWRITE_SYSTEM_PROMPT,
        build_rewrite_prompt(
            goal,
            clause_text,
            json.dumps(context_payload, ensure_ascii=False),
        ),
        chain_name="rewrite_clause",
    )
