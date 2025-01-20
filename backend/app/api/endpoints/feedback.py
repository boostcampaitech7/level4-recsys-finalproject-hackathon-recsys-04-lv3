# app/api/endpoints/feedback.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from ...db.database import get_db
from ...models.analysis import Analysis
from ...models.feedback import Feedback
from ...services.rag_service import RAGService
import uuid

router = APIRouter()

# 모델 정의
class FeedbackCreate(BaseModel):
    analyze_id: str
    rating: int
    comment: Optional[str] = None

class NoteContent(BaseModel):
    content: str
    title: Optional[str] = None
    subjects_id: Optional[str] = None

def generate_id():
    return str(uuid.uuid4())[:8]

# RAG 기반 피드백 생성
@router.post("/notes/{note_id}/feedback")
async def create_note_feedback(
    note_id: str,
    note: NoteContent,
    db: Session = Depends(get_db)
):
    try:
        # RAG 서비스 초기화
        rag_service = RAGService()
        
        # 기본 피드백과 RAG 기반 피드백 생성
        basic_feedback, rag_feedback = await rag_service.generate_feedback(note.content)

        # 기본 분석 결과 저장
        basic_analysis = Analysis(
            analyze_id=generate_id(),
            note_id=note_id,
            result=basic_feedback,
            rag_id=None
        )
        
        # RAG 기반 분석 결과 저장
        rag_id = generate_id()
        rag_analysis = Analysis(
            analyze_id=generate_id(),
            note_id=note_id,
            result=rag_feedback,
            rag_id=rag_id
        )
        
        db.add(basic_analysis)
        db.add(rag_analysis)
        db.commit()
        
        return {
            "note_id": note_id,
            "content": note.content,
            "basic_feedback": basic_feedback,
            "rag_feedback": rag_feedback,
            "basic_analyze_id": basic_analysis.analyze_id,
            "rag_analyze_id": rag_analysis.analyze_id,
            "saved_to_db": True
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 피드백 평가 저장
@router.post("/feedback")
async def create_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    try:
        # 분석 결과 확인
        analysis = db.query(Analysis).filter(
            Analysis.analyze_id == feedback.analyze_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # 피드백 저장
        feedback_record = Feedback(
            feedback_id=generate_id(),
            analyze_id=feedback.analyze_id,
            rating=feedback.rating,
            comment=feedback.comment
        )
        
        db.add(feedback_record)
        db.commit()

        return {"feedback_id": feedback_record.feedback_id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# 피드백 비교 조회
@router.get("/feedback/compare/{note_id}")
async def compare_feedback(
    note_id: str,
    db: Session = Depends(get_db)
):
    try:
        # RAG 적용 전/후 분석 결과와 피드백 조회
        results = db.query(
            Analysis, Feedback
        ).outerjoin(  # outer join으로 변경하여 피드백이 없는 분석 결과도 포함
            Feedback, Analysis.analyze_id == Feedback.analyze_id
        ).filter(
            Analysis.note_id == note_id
        ).all()

        return {
            "rag_results": [
                {
                    "analyze_id": r.Analysis.analyze_id,
                    "result": r.Analysis.result,
                    "feedback": {
                        "rating": r.Feedback.rating if r.Feedback else None,
                        "comment": r.Feedback.comment if r.Feedback else None
                    }
                }
                for r in results if r.Analysis.rag_id is not None
            ],
            "non_rag_results": [
                {
                    "analyze_id": r.Analysis.analyze_id,
                    "result": r.Analysis.result,
                    "feedback": {
                        "rating": r.Feedback.rating if r.Feedback else None,
                        "comment": r.Feedback.comment if r.Feedback else None
                    }
                }
                for r in results if r.Analysis.rag_id is None
            ],
            "note_id": note_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 특정 분석 결과 조회
@router.get("/feedback/{analyze_id}")
async def get_feedback(
    analyze_id: str,
    db: Session = Depends(get_db)
):
    try:
        analysis = db.query(Analysis).filter(
            Analysis.analyze_id == analyze_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
            
        feedback = db.query(Feedback).filter(
            Feedback.analyze_id == analyze_id
        ).first()

        return {
            "analyze_id": analyze_id,
            "result": analysis.result,
            "is_rag": analysis.rag_id is not None,
            "feedback": {
                "rating": feedback.rating if feedback else None,
                "comment": feedback.comment if feedback else None
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))