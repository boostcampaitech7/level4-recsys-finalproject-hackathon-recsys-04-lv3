from app.core.config import settings
from app.services.rag_service import add_document, initialize_pinecone
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/vectorstore")
async def post_create_vectorstore():
    """벡터 저장소를 초기화하고 생성합니다."""
    try:
        initialize_pinecone()

        return {"message": "Vector store initialized successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def check_vectorstore_status():
    """벡터 저장소의 상태를 확인합니다."""
    try:
        pc = initialize_pinecone()
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        stats = index.describe_index_stats()

        return {
            "index_name": settings.PINECONE_INDEX_NAME,
            "total_vector_count": stats.total_vector_count,
            "dimension": stats.dimension,
            "namespaces": stats.namespaces,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/document")
async def add_reference_document(directory_path: str, subject: str = "default"):
    """
    /data 폴더의 PDF 문서들을 벡터 저장소에 추가합니다.

    Parameters:
    - subject: 문서 주제 (기본값: "default")
    """
    try:
        # 프로젝트 루트의 data 폴더 경로 설정
        # directory_path = "./data"  # 고정된 경로 사용

        add_document(directory_path, subject)

        return {
            "message": "Documents added successfully",
            "directory": directory_path,
            "subject": subject,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to add documents: {str(e)}"
        )
