# app/api/endpoints/user.py
from app.api import deps
from app.models.analysis import Analysis
from app.models.note import Note
from app.models.ox import OX
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/{user_id}/feedbacks")
def get_user_feedbacks(user_id: str, db: Session = Depends(deps.get_db)):
    feedbacks = (
        db.query(Analysis, Note)
        .join(Note, Analysis.note_id == Note.note_id)
        .filter(Note.user_id == user_id)
        .order_by(Analysis.created_at.desc())
        .all()
    )

    return {
        "feedbacks": [
            {
                "note_title": feedback.Note.title,
                "feedback": feedback.Analysis.feedback,
                "created_at": feedback.Analysis.created_at,
            }
            for feedback in feedbacks
        ]
    }


@router.get("/{user_id}/quizzes")
def get_user_quizzes(user_id: str, db: Session = Depends(deps.get_db)):
    quizzes = db.query(OX).filter(OX.user_id == user_id, OX.del_yn == "N").order_by(OX.created_at.desc()).all()

    return {
        "quizzes": [
            {
                "title": quiz.note_id,
                "question": quiz.ox_contents,
                "answer": quiz.ox_answer if quiz.used_yn == "Y" else None,
                "explanation": quiz.ox_explanation if quiz.used_yn == "Y" else None,
                "is_correct": quiz.correct_yn if quiz.used_yn == "Y" else None,
                "created_at": quiz.created_at,
            }
            for quiz in quizzes
        ]
    }
