from app.api import deps
from app.models.ox import OX
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

router = APIRouter()


class QuizAnswer(BaseModel):
    user_id: str
    ox_id: str
    user_answer: str


@router.get("/next")
def next_quiz(user_id: str, note_id: str, db: Session = Depends(deps.get_db)):
    # 모든 퀴즈 초기화 확인
    all_used = (
        not db.query(OX)
        .filter(OX.user_id == user_id, OX.note_id == note_id, OX.del_yn == "N", OX.used_yn == "N")
        .first()
    )

    # 모든 퀴즈가 used면 초기화
    if all_used:
        db.query(OX).filter(OX.user_id == user_id, OX.note_id == note_id, OX.del_yn == "N").update({"used_yn": "N"})
        db.commit()

    # 초기화 후 랜덤 퀴즈 가져오기
    quiz = (
        db.query(OX)
        .filter(OX.user_id == user_id, OX.note_id == note_id, OX.used_yn == "N", OX.del_yn == "N")
        .order_by(func.random())
        .first()
    )

    if not quiz:
        raise HTTPException(status_code=400, detail="No quizzes available")

    return {"quiz": {"question": quiz.ox_contents, "ox_id": quiz.ox_id}}


@router.post("/solve")
async def solve_quiz(
    user_id: str = Form(...), ox_id: str = Form(...), user_answer: str = Form(...), db: Session = Depends(deps.get_db)
):
    quiz = db.query(OX).filter(OX.ox_id == ox_id, OX.used_yn == "N", OX.del_yn == "N").first()

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct = "Y" if quiz.ox_answer == user_answer else "N"
    quiz.correct_yn = correct
    quiz.used_yn = "Y"
    db.commit()

    return {
        "result": {
            "is_correct": "정답입니다!" if correct == "Y" else "틀렸습니다",
            "correct_answer": quiz.ox_answer,
            "explanation": quiz.ox_explanation,
        }
    }


@router.get("/{note_id}/quizzes")
def get_note_quizzes(note_id: str, user_id: str, db: Session = Depends(deps.get_db)):
    quizzes = db.query(OX).filter(OX.note_id == note_id, OX.user_id == user_id, OX.del_yn == "N").all()

    return {
        "quizzes": [{"ox_id": quiz.ox_id, "question": quiz.ox_contents, "used_yn": quiz.used_yn} for quiz in quizzes]
    }
