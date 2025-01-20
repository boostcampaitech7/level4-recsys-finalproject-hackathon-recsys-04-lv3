# app/scripts/initialize_knowledge_base.py
import asyncio
import os
from ..services.document_loader import DocumentLoader

async def init_knowledge_base():
    try:
        # DocumentLoader 인스턴스 생성
        loader = DocumentLoader()
        
        # 문서 처리 및 Pinecone에 저장
        await loader.process_documents()
        
        print("Knowledge base initialization completed successfully!")
        
    except Exception as e:
        print(f"Error initializing knowledge base: {str(e)}")
        raise

def main():
    # 스크립트가 프로젝트 루트에서 실행되는지 확인
    if not os.path.exists("app/data/documents"):
        print("Error: Please run this script from the project root directory")
        return
    
    # 비동기 초기화 함수 실행
    asyncio.run(init_knowledge_base())

if __name__ == "__main__":
    main()