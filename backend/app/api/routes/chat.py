"""Analyst chat with extractive policy answers and traceable evidence."""
import re

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import Principal, require
from app.db.session import get_db
from app.rag.service import rag_service
from app.schemas.domain import ChatRequest
from app.services.investigation import investigate

router = APIRouter(prefix="/chat", tags=["chat"])


def policy_answer(message: str) -> dict:
    # Extractive mode deliberately avoids inventing eligibility or provider status.
    retrieved = rag_service.search(message, 4)
    if not retrieved:
        return {
            "mode": "general_rag",
            "answer": (
                "I could not find supporting policy evidence for that question. "
                "Please specify the payment method, whether this was a transfer or "
                "merchant purchase, and the failure or refund status. An analyst "
                "should review cases without an applicable source."
            ),
            "sources": [],
        }

    sources = []
    passages = []
    # Return complete paragraphs instead of cutting a sentence that may contain
    # an exception. The selected passages are evidence, not executed instructions.
    for index, item in enumerate(retrieved[:2], start=1):
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        title = str(item.get("document", "Policy reference")).replace("-", " ")
        passages.append(f"[{index}] {title}\n{text}")
        source = {key: value for key, value in item.items() if key != "text"}
        # Headings may be split from a document's source URL by the chunker.
        # Include provenance from that same local document when available.
        provenance = "\n".join(
            chunk.text for chunk in rag_service.chunks
            if chunk.document == item.get("document")
        )
        source["urls"] = sorted(set(
            match.rstrip(".,;)")
            for match in re.findall(r"https://[^\s<>]+", text + "\n" + provenance)
        ))
        source["excerpt"] = text
        sources.append(source)

    if not passages:
        return {
            "mode": "general_rag",
            "answer": "The retrieved references contain no usable policy text. Request analyst review.",
            "sources": [],
        }
    return {
        "mode": "general_rag",
        "answer": (
            "Relevant passages from the policy knowledge base:\n\n"
            + "\n\n".join(passages)
            + "\n\nThese passages provide general guidance. Confirm the incident type "
            "and current provider evidence before applying a deadline or recommending "
            "an action. This response does not confirm bank status or initiate a refund."
        ),
        "sources": sources,
    }


@router.post("")
async def chat(
    b: ChatRequest,
    db: AsyncSession = Depends(get_db),
    _: Principal = Depends(require("analyst")),
):
    if b.transaction_id:
        investigation = await investigate(db, b.transaction_id, b.message)
        return {
            "mode": "transaction_investigation",
            "investigation_id": investigation.id,
            "answer": investigation.summary,
            "sources": investigation.sources,
        }
    return policy_answer(b.message)
