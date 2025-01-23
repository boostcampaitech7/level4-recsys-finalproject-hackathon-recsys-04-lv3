# app/api/endpoints/rag.py
import uuid

from app.api import deps
from app.core.config import settings  # settings import 추가
from app.models.analysis import Analysis
from app.models.note import Note
from app.services.rag_service import analysis_chunk, initialize_pinecone, add_document
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()

class VectorStoreInput(BaseModel):
    file_path: str

@router.post("/vectorstore")
async def post_create_vectorstore(input_data: VectorStoreInput):
    """벡터 저장소를 초기화하고 생성합니다."""
    try:
        print(f"input data: {input_data}")
        print(input_data.file_path)

        result = initialize_pinecone()
        print(result)

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
            "namespaces": stats.namespaces
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/document")
async def add_reference_document(subject: str = "default"):
    """
    /data 폴더의 PDF 문서들을 벡터 저장소에 추가합니다.
    
    Parameters:
    - subject: 문서 주제 (기본값: "default")
    """
    try:
        # 프로젝트 루트의 data 폴더 경로 설정
        directory_path = "./data"  # 고정된 경로 사용
        
        vectorstore = add_document(directory_path, subject)
        
        return {
            "message": "Documents added successfully",
            "directory": directory_path,
            "subject": subject
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add documents: {str(e)}"
        )