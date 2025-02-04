from app.api import deps
from app.models.multiple import MultipleChoice
from app.models.note import Note
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


@router.get("/next/multiple")
def next_multiple_choice_quiz(user_id: str, db: Session = Depends(deps.get_db)):
    try:
        # 해당 유저의 모든 미사용 퀴즈 중에서 랜덤으로 하나 선택
        quiz = (
            db.query(MultipleChoice)
            .filter(MultipleChoice.user_id == user_id, MultipleChoice.used_yn == "N", MultipleChoice.del_yn == "N")
            .order_by(func.random())
            .first()
        )

        if not quiz:
            # 모든 퀴즈가 사용되었다면 초기화
            db.query(MultipleChoice).filter(MultipleChoice.user_id == user_id, MultipleChoice.del_yn == "N").update(
                {"used_yn": "N"}
            )
            db.commit()

            # 다시 퀴즈 가져오기
            quiz = (
                db.query(MultipleChoice)
                .filter(MultipleChoice.user_id == user_id, MultipleChoice.used_yn == "N", MultipleChoice.del_yn == "N")
                .order_by(func.random())
                .first()
            )

        if not quiz:
            return {"quiz": None, "message": "사용 가능한 퀴즈가 없습니다."}

        return {
            "quiz": {
                "quiz_id": quiz.quiz_id,
                "question": quiz.quiz_contents,
                "option1": quiz.option1,
                "option2": quiz.option2,
                "option3": quiz.option3,
                "option4": quiz.option4,
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/solve/multiple")
async def solve_multiple_choice_quiz(
    user_id: str = Form(...), quiz_id: str = Form(...), user_answer: str = Form(...), db: Session = Depends(deps.get_db)
):
    quiz = (
        db.query(MultipleChoice)
        .filter(MultipleChoice.quiz_id == quiz_id, MultipleChoice.used_yn == "N", MultipleChoice.del_yn == "N")
        .first()
    )

    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    correct = "Y" if quiz.quiz_answer == user_answer else "N"
    quiz.correct_yn = correct
    quiz.used_yn = "Y"
    db.commit()

    return {
        "result": {
            "is_correct": "정답입니다!" if correct == "Y" else "틀렸습니다",
            "correct_answer": quiz.quiz_answer,
            "explanation": quiz.quiz_explanation,
        }
    }


@router.get("/multiple/by-subject/{subject_id}")
def get_multiple_by_subject(subject_id: str, user_id: str, db: Session = Depends(deps.get_db)):
    try:
        # 해당 과목의 모든 풀지 않은 문제들을 한번에 가져오기 (메모 구분 없이)
        quizzes = (
            db.query(MultipleChoice)
            .join(Note, MultipleChoice.note_id == Note.note_id)
            .filter(
                MultipleChoice.user_id == user_id,
                MultipleChoice.del_yn == "N",
                MultipleChoice.used_yn == "N",
                Note.subjects_id == subject_id,
            )
            .order_by(func.random())  # 랜덤으로 섞기
            .all()
        )

        if not quizzes:
            return {"quizzes": [], "message": "해당 과목의 모든 문제를 풀었습니다!", "redirect": True}

        # 모든 문제 반환 (제한 없이)
        return {
            "quizzes": [
                {
                    "quiz_id": quiz.quiz_id,
                    "question": quiz.quiz_contents,
                    "option1": quiz.option1,
                    "option2": quiz.option2,
                    "option3": quiz.option3,
                    "option4": quiz.option4,
                }
                for quiz in quizzes
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
def get_quiz_history(user_id: str, db: Session = Depends(deps.get_db)):
    try:
        quizzes = (
            db.query(MultipleChoice, Note.subjects_id)
            .join(Note, MultipleChoice.note_id == Note.note_id)
            .filter(
                MultipleChoice.user_id == user_id,
                MultipleChoice.used_yn == "Y",  # 푼 문제만 가져오기
                MultipleChoice.del_yn == "N",
            )
            .order_by(MultipleChoice.created_at.desc())  # 최신순 정렬
            .all()
        )

        return {
            "quizzes": [
                {
                    "quiz_id": quiz.MultipleChoice.quiz_id,
                    "subject": quiz.subjects_id,
                    "question": quiz.MultipleChoice.quiz_contents,
                    "options": {
                        "1": quiz.MultipleChoice.option1,
                        "2": quiz.MultipleChoice.option2,
                        "3": quiz.MultipleChoice.option3,
                        "4": quiz.MultipleChoice.option4,
                    },
                    "answer": quiz.MultipleChoice.quiz_answer,
                    "correct_yn": quiz.MultipleChoice.correct_yn,
                    "explanation": quiz.MultipleChoice.quiz_explanation,
                    "solved_at": quiz.MultipleChoice.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for quiz in quizzes
            ]
        }

    except Exception as e:
        print(f"Error in get_quiz_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_quizzes(user_id: str = Form(...), subject_id: str = Form(None), db: Session = Depends(deps.get_db)):
    try:
        if subject_id:
            # 특정 과목의 노트 ID들을 먼저 가져옴
            note_ids = db.query(Note.note_id).filter(Note.subjects_id == subject_id, Note.user_id == user_id).all()
            note_ids = [note[0] for note in note_ids]

            # 해당 노트들의 퀴즈를 리셋
            db.query(MultipleChoice).filter(
                MultipleChoice.user_id == user_id, MultipleChoice.note_id.in_(note_ids)
            ).update({"used_yn": "N"}, synchronize_session=False)
        else:
            # 모든 퀴즈 리셋
            db.query(MultipleChoice).filter(MultipleChoice.user_id == user_id).update(
                {"used_yn": "N"}, synchronize_session=False
            )

        db.commit()
        return {"message": "Successfully reset quizzes"}

    except Exception as e:
        print(f"Error resetting quizzes: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
