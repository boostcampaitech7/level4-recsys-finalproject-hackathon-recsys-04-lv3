from pinecone import Pinecone
from services.upstage_api import get_embeddings

async def generate_rag_feedback(text: str):
    # 1. 텍스트 임베딩 생성
    embeddings = await get_embeddings(text)
    
    # 2. Pinecone에서 관련 문서 검색
    similar_docs = pc.query(embeddings)
    
    # 3. Upstage API로 피드백 생성
    feedback = await generate_feedback_with_context(text, similar_docs)
    return feedback