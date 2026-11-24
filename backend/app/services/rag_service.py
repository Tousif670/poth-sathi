import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.core.llm_client import LLMToolCall
from app.models.chat import ChatResponse, ChatSource
from app.models.kb import KBChunkDoc
from app.repositories.kb_repository import KBRepository

SEED_KB_PATH = Path(__file__).resolve().parent.parent.parent.parent / "seed" / "kb_chunks.json"

AI_REST_MESSAGE_BN = "আমাদের AI সহকারী এখন বিশ্রামে আছে। নিচের তথ্যগুলো দেখুন।"
AI_REST_MESSAGE_EN = "Our AI assistant is resting. See the verified travel information below."


@dataclass
class RAGChunkMatch:
    chunk_id: str
    category: str
    text: str
    source: str
    is_verified: bool
    relevance_score: float


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b, strict=False))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _tokenize(text: str) -> list[str]:
    return [tok for tok in re.split(r"[\s,।?!.;:()\"']+", text.lower()) if len(tok) >= 2]


class RAGService:
    """In-memory RAG index built from kb_chunks with vector cosine similarity,
    keyword matching fallback, and keyword intent router (D6, D7, docs/ai-spec.md §7 & §11).
    """

    def __init__(
        self,
        kb_repository: KBRepository | None = None,
        initial_chunks: list[KBChunkDoc] | None = None,
    ) -> None:
        self._repo = kb_repository
        self._chunks: list[KBChunkDoc] = initial_chunks if initial_chunks is not None else []
        if not self._chunks:
            self.rebuild_index()

    def rebuild_index(self) -> int:
        if self._repo is not None:
            try:
                loaded = self._repo.list_all()
                if loaded:
                    self._chunks = loaded
                    return len(self._chunks)
            except Exception:
                pass

        if SEED_KB_PATH.exists():
            raw = json.loads(SEED_KB_PATH.read_text(encoding="utf-8"))
            self._chunks = [KBChunkDoc.model_validate(item) for item in raw]
        return len(self._chunks)

    def search(
        self,
        query: str,
        lang: Literal["bn", "en"] = "bn",
        query_embedding: list[float] | None = None,
        top_k: int = 3,
        threshold: float = 0.65,
    ) -> list[RAGChunkMatch]:
        if not self._chunks:
            self.rebuild_index()

        results: list[RAGChunkMatch] = []

        # 1. Vector cosine similarity search when embeddings are present
        if query_embedding:
            for chunk in self._chunks:
                if chunk.embedding:
                    sim = _cosine_similarity(query_embedding, chunk.embedding)
                    if sim >= threshold:
                        text_str = chunk.text.bn if lang == "bn" else chunk.text.en
                        results.append(
                            RAGChunkMatch(
                                chunk_id=chunk.chunk_id or chunk.id,
                                category=chunk.category,
                                text=text_str,
                                source=chunk.source,
                                is_verified=chunk.is_verified,
                                relevance_score=round(sim, 3),
                            )
                        )
            if results:
                results.sort(key=lambda m: m.relevance_score, reverse=True)
                return results[:top_k]

        # 2. Keyword matching fallback over chunk text and category
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        for chunk in self._chunks:
            haystack = f"{chunk.text.bn} {chunk.text.en} {chunk.category}".lower()
            hits = sum(1 for tok in query_tokens if tok in haystack)
            if hits > 0:
                score = min(1.0, 0.65 + (hits / max(len(query_tokens), 1)) * 0.35)
                text_str = chunk.text.bn if lang == "bn" else chunk.text.en
                results.append(
                    RAGChunkMatch(
                        chunk_id=chunk.chunk_id or chunk.id,
                        category=chunk.category,
                        text=text_str,
                        source=chunk.source,
                        is_verified=chunk.is_verified,
                        relevance_score=round(score, 3),
                    )
                )

        results.sort(key=lambda m: m.relevance_score, reverse=True)
        return results[:top_k]

    def route_keyword_intent(self, query: str) -> list[LLMToolCall]:
        """Simple keyword intent router for fallback when Gemini fails or quota is exhausted."""
        q = query.lower()
        calls: list[LLMToolCall] = []

        area: str | None = None
        if "kolatoli" in q or "কলাতলী" in q:
            area = "kolatoli"
        elif "sugandha" in q or "সুগন্ধা" in q:
            area = "sugandha"
        elif "laboni" in q or "লাবণী" in q:
            area = "laboni"

        if any(k in q for k in ["hotel", "হোটেল", "resort", "রিসোর্ট", "রুম", "room"]):
            args: dict[str, Any] = {}
            if area:
                args["area"] = area
            calls.append(LLMToolCall(name="search_hotels", args=args))
        elif any(k in q for k in ["fare", "ভাড়া", "cng", "সিএনজি", "tomtom", "টমটম", "রিকশা"]):
            calls.append(
                LLMToolCall(
                    name="calculate_fare",
                    args={"origin": area or "kolatoli", "destination": "laboni"},
                )
            )
        elif any(k in q for k in ["flag", "পতাকা", "beach", "সৈকত", "সমুদ্র", "সাঁতার", "swim"]):
            args = {"zone": area} if area else {}
            calls.append(LLMToolCall(name="get_beach_status", args=args))
        elif any(
            k in q
            for k in [
                "hospital",
                "হাসপাতাল",
                "pharmacy",
                "ফার্মেসি",
                "atm",
                "এটিএম",
                "police",
                "পুলিশ",
                "mosque",
                "মসজিদ",
            ]
        ):
            cat = "all"
            if "hospital" in q or "হাসপাতাল" in q:
                cat = "hospital"
            elif "pharmacy" in q or "ফার্মেসি" in q:
                cat = "pharmacy"
            elif "atm" in q or "এটিএম" in q:
                cat = "atm"
            elif "police" in q or "পুলিশ" in q:
                cat = "police"
            elif "mosque" in q or "মসজিদ" in q:
                cat = "mosque"
            calls.append(LLMToolCall(name="find_nearby", args={"category": cat}))

        return calls

    def fallback_answer(
        self,
        query: str,
        lang: Literal["bn", "en"] = "bn",
        session_id: str | None = None,
        tool_executor: Any | None = None,
    ) -> ChatResponse:
        """Execute Fallback Chain (docs/ai-spec.md §11):
        1. Keyword intent router -> Service tool call
        2. RAG chunk search
        3. Polite 'AI is resting' message
        """
        cards = []
        sources: list[ChatSource] = []
        tool_names: list[str] = []
        lines: list[str] = []

        # Step 1: Keyword intent router
        intent_calls = self.route_keyword_intent(query)
        if intent_calls and tool_executor is not None:
            exec_res = tool_executor.execute_all(intent_calls, lang=lang)
            cards.extend(exec_res.cards)
            sources.extend(exec_res.sources)
            tool_names.extend(exec_res.tool_names)
            lines.extend(exec_res.summary_lines)

        # Step 2: RAG search over kb_chunks
        kb_matches = self.search(query=query, lang=lang, top_k=3)
        for m in kb_matches:
            lines.append(m.text)
            sources.append(
                ChatSource(
                    label=f"Knowledge Base ({m.category})",
                    source_id=f"kb_chunks/{m.chunk_id}",
                    is_verified=m.is_verified,
                )
            )

        rest_header = AI_REST_MESSAGE_BN if lang == "bn" else AI_REST_MESSAGE_EN
        if lines:
            combined = f"{rest_header}\n\n" + "\n".join(lines[:3])
        else:
            combined = rest_header

        return ChatResponse(
            answer_text=combined,
            language=lang,
            session_id=session_id,
            cards=cards,
            sources=sources,
            severity="warning",
            tool_calls_used=tool_names,
            fallback_used=True,
            safety_triggered=False,
            is_ai_resting=True,
        )


global_rag_service = RAGService()
