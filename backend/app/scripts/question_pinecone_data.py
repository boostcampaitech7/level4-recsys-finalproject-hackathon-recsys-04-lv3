# app/scripts/check_pinecone_data.py
import asyncio
from ..services.document_loader import DocumentLoader

async def check_pinecone_data():
    try:
        loader = DocumentLoader()
        
        # 실제 질문으로 검색
        query = "지구과학이 뭐에요?"
        print(f"\n검색 질문: {query}")
        
        results = await loader.search_similar(query, top_k=3)
        
        print("\n검색 결과:")
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"Content: {result['content'][:200]}...")
            print(f"Source: {result['source']}")
            print(f"Similarity Score: {result['score']}")

    except Exception as e:
        print(f"Error checking Pinecone data: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_pinecone_data())