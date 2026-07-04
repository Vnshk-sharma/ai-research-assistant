"""
Chat service — the core RAG loop: retrieve relevant chunks, build a
context window, ask the reasoning engine, attach citations, persist the
exchange to chat history.
"""

from sqlalchemy.orm import Session

from retrieval.retriever import get_retriever
from summarization.reasoning_engine import get_reasoning_engine
from utils.citation import build_citations
from models.db_models import ChatMessage
from models.schemas import ChatResponse

CONTEXT_CHAR_LIMIT = 3000


class ChatService:
    def __init__(self):
        self.retriever = get_retriever()
        self.reasoner = get_reasoning_engine()

    def ask(self, db: Session, query: str, paper_id: str | None, top_k: int) -> ChatResponse:
        retrieved = self.retriever.retrieve(db, query, top_k=top_k, paper_id=paper_id)

        if not retrieved:
            answer = (
                "I couldn't find any relevant content in the uploaded papers "
                "to answer that. Try rephrasing, or make sure a paper has "
                "finished processing."
            )
            citations = []
        else:
            context = "\n\n---\n\n".join(c.text for c in retrieved)[:CONTEXT_CHAR_LIMIT]
            answer = self.reasoner.answer_question(query, context)
            citations = build_citations(retrieved)

        db.add(ChatMessage(paper_id=paper_id, role="user", content=query))
        db.add(
            ChatMessage(
                paper_id=paper_id,
                role="assistant",
                content=answer,
                citations=[c.model_dump() for c in citations],
            )
        )
        db.commit()

        return ChatResponse(answer=answer, citations=citations)


_chat_service_instance: ChatService | None = None


def get_chat_service() -> ChatService:
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance
