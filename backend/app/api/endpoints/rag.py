#app/api/endpoints/rag.py
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session
from typing import List
from app.core.config import settings
from .document_loader import DocumentLoader

router = APIRouter()

class RAGService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.UPSTAGE_API_KEY,
            base_url=settings.UPSTAGE_BASE_URL
        )
        self.doc_loader = DocumentLoader()
    
    async def get_relevant_documents(self, query: str, db: Session) -> List[str]:
        # 1. 질문 텍스트의 임베딩 생성
        query_embedding = self.client.embeddings.create(
            input=query,
            model="embedding-query"
        ).data[0].embedding

        # 2. 기존 문서들의 임베딩과 비교하여 가장 관련성 높은 문서 검색
        # (이미 저장된 문서들의 임베딩과 코사인 유사도 계산)
        relevant_docs = db.query(Document).order_by(
            cosine_similarity(Document.embedding, query_embedding)
        ).limit(3).all()
        
        return [doc.content for doc in relevant_docs]

    async def generate_response(self, query: str, context: List[str]) -> str:
        # 관련 문서들을 컨텍스트로 활용하여 응답 생성
        context_text = "\n".join(context)
        response = self.client.chat.completions.create(
            model="solar-mini",
            messages=[
                {"role": "system", "content": f"다음 정보를 바탕으로 질문에 답변하세요:\n\n{context_text}"},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content

@router.post("/analyze")
async def analyze_note(note_id: str, db: Session = Depends(get_db)):
    # 1. 노트(질문) 가져오기
    note = db.query(Note).filter(Note.note_id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    rag_service = RAGService()
    
    # 2. 질문과 관련된 문서 검색
    relevant_docs = await rag_service.get_relevant_documents(note.content, db)
    
    # 3. RAG 기반 응답 생성
    rag_response = await rag_service.generate_response(note.content, relevant_docs)
    
    # 4. RAG 없이 직접 응답 생성 (비교용)
    direct_response = await rag_service.generate_response(note.content, [])
    
    # 5. 결과 저장
    analysis = Analysis(
        analyze_id=generate_id(),
        note_id=note_id,
        rag_result=rag_response,
        direct_result=direct_response
    )
    db.add(analysis)
    db.commit()

    return {
        "note_id": note_id,
        "question": note.content,
        "rag_answer": rag_response,
        "direct_answer": direct_response
    }