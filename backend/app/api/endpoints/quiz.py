# backend/app/api/endpoints/quiz.py
from app.api import deps
from app.models.ox import OX  # OX 모델 import
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# 1. 첫 번째 문제 가져오기: 아직 푼 적 없는 문제 중 첫 번째 문제 가져오기
@router.get("/next")
def next_quiz(user_id: str, db: Session = Depends(deps.get_db)):
    # 사용자가 푼 적 없는 문제 중에서 하나를 가져옴
    quiz = db.query(OX).filter(OX.used_yn == "N", OX.del_yn == "N").first()
    
    if not quiz:
        raise HTTPException(status_code=400, detail="No quizzes available")
    
    # 푼 문제에 대한 정보를 반환 (답을 제출할 수 있도록 ox_id 포함)
    return {
        "message": "Next quiz fetched successfully",
        "quiz": {
            "question": quiz.ox_contents,
            "ox_id": quiz.ox_id
        }
    }

# 2. 문제에 대한 답 제출하기: 답을 제출하고 정답 여부 및 해설 반환
@router.post("/solve")
def solve_quiz(user_id: str, ox_id: str, user_answer: str, db: Session = Depends(deps.get_db)):
    # 사용자가 제출한 ox_id에 해당하는 문제를 찾음
    quiz = db.query(OX).filter(OX.ox_id == ox_id, OX.used_yn == "N", OX.del_yn == "N").first()
    
    if not quiz:
        raise HTTPException(status_code=400, detail=f"Quiz {ox_id} not found or already solved")
    
    # 정답 비교
    correct = "Y" if quiz.ox_answer == user_answer else "N"
    
    # 정답 여부 업데이트
    quiz.correct_yn = correct
    quiz.used_yn = "Y"  # 문제를 푼 후 used_yn을 'Y'로 변경
    db.add(quiz)
    db.commit()
    
    # 해설 내용
    explanation = quiz.ox_explanation or "No explanation provided"

    return {
        "message": "Quiz solved",
        "result": {
            "question": quiz.ox_contents,
            "your_answer": user_answer,
            "correct_answer": quiz.ox_answer,
            "is_correct": "Correct!" if correct == "Y" else "Incorrect",
            "explanation": explanation
        }
    }
