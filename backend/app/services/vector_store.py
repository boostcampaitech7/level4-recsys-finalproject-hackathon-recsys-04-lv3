# app/services/vector_store.py
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict

class VectorStore:
    def __init__(self):
        self.pc = Pinecone(
            api_key="YOUR_PINECONE_API_KEY"
        )
        # 인덱스가 없으면 생성
        if "solar-teacher" not in self.pc.list_indexes():
            self.pc.create_index(
                name="solar-teacher",
                dimension=1536,  # OpenAI embedding 차원 수
                spec=ServerlessSpec(cloud="aws", region="us-west-2")
            )
        self.index = self.pc.Index("solar-teacher")

    async def store_embeddings(self, documents: List[Dict]):
        # 문서와 임베딩을 Pinecone에 저장
        vectors = []
        for i, doc in enumerate(documents):
            vectors.append({
                "id": f"doc_{i}",
                "values": doc["embedding"],
                "metadata": {
                    "text": doc["content"],
                    "source": doc["source"]
                }
            })
        
        # 배치로 벡터 업로드
        self.index.upsert(vectors=vectors)

    async def search_similar(self, query_embedding: List[float], top_k: int = 3):
        # 쿼리 벡터와 가장 유사한 문서 검색
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        return [
            {
                "content": match.metadata["text"],
                "score": match.score,
                "source": match.metadata["source"]
            }
            for match in results.matches
        ]