import ast
import json
import os
import time
import traceback
import uuid
from typing import Optional
from datetime import date, timedelta

from app.api import deps
from app.models.analysis import Analysis
from app.models.multiple import MultipleChoice
from app.models.note import Note
from app.models.ox import OX
from app.services.ocr_service import perform_ocr
from app.services.rag_service import analysis_chunk
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from sqlalchemy import text

router = APIRouter()


@router.post("/text")
async def create_text_note(
    title: str = Form(...),
    subjects_id: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(deps.get_db),
    user_id: Optional[str] = Form(...),
):
    try:
        note_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # 노트 저장
        if user_id:
            note = Note(
                note_id=note_id,
                user_id=user_id,
                subjects_id=subjects_id,
                title=title,
                raw_text=content,
                ocr_yn="N",
                del_yn="N",
            )
            db.add(note)
            db.commit()

        # RAG 분석 수행
        result = analysis_chunk(content)
        print("Analysis Result:", result)

        # Note db subject 수정
        if subjects_id == "선택 안함":
            subjects_id = result["subjects_id"]
            note.subjects_id = subjects_id
            db.commit()

        # 분석 결과 저장
        if user_id:
            analysis = Analysis(
                analyze_id=str(uuid.uuid4())[:8],
                note_id=note_id,
                chunk_num=0,
                rag_id=result["rag_id"],
                feedback=result["response"],
            )
            db.add(analysis)
            db.commit()

        # O/X 퀴즈 생성
        quizzes = result.get("quiz", [])
        print("Quizzes:", quizzes)
        print("Type of quizzes:", type(quizzes))

        if isinstance(quizzes, str):
            try:
                quizzes = json.loads(quizzes)
                print("Quizzes after JSON parsing:", quizzes)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                quizzes = []

        if isinstance(quizzes, dict):
            quiz_list = quizzes.get("quiz", [])
        elif isinstance(quizzes, list):
            quiz_list = quizzes
        else:
            print(
                "Invalid structure of quizzes. Expected a string, dictionary, or list."
            )
            quiz_list = []

        for quiz in quiz_list:
            print("Processing quiz:", quiz)
            if not isinstance(quiz, dict):
                try:
                    quiz = ast.literal_eval(quiz)
                except (ValueError, SyntaxError) as e:
                    print(f"Error parsing quiz: {quiz} - {e}")
                    continue

            try:
                ox_id = str(uuid.uuid4())[:8]
                ox = OX(
                    ox_id=ox_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get("rag_id"),
                    ox_contents=quiz["question"],
                    ox_answer=quiz["answer"],
                    ox_explanation=quiz["explanation"],
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(ox)
                print(f"Successfully added OX with ox_id={ox_id} to session")
            except Exception as e:
                print(f"Error saving quiz: {e}")
                print(traceback.format_exc())
                continue

        # 객관식 퀴즈 생성 및 저장
        multiple_quizzes = result.get("multiple", [])
        # print("Multiple Choice Quizzes:", multiple_quizzes)
        # print("Type of multiple quizzes:", type(multiple_quizzes))

        if isinstance(multiple_quizzes, str):
            try:
                multiple_quizzes = json.loads(multiple_quizzes)
                print("Multiple quizzes after JSON parsing:", multiple_quizzes)
            except json.JSONDecodeError as e:
                print(f"Error decoding multiple JSON: {e}")
                multiple_quizzes = []

        multiple_list = []
        if isinstance(multiple_quizzes, dict):
            multiple_list = multiple_quizzes.get("questions", [])
        elif isinstance(multiple_quizzes, list):
            multiple_list = multiple_quizzes

        for quiz in multiple_list:
            # print("Processing multiple quiz:", quiz)
            try:
                quiz_id = str(uuid.uuid4())[:8]
                multiple = MultipleChoice(
                    quiz_id=quiz_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get("rag_id"),
                    quiz_contents=quiz["question"],
                    option1=quiz["option1"],
                    option2=quiz["option2"],
                    option3=quiz["option3"],
                    option4=quiz["option4"],
                    quiz_answer=quiz["answer"],
                    quiz_explanation=quiz["explanation"],
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(multiple)
                print(f"Successfully added multiple choice quiz with quiz_id={quiz_id}")
            except Exception as e:
                print(f"Error saving multiple quiz: {e}")
                print(traceback.format_exc())
                continue

        # 커밋 실행
        try:
            print("Attempting to commit changes to the database...")
            db.commit()
            print("Database commit successful!")
        except Exception as commit_error:
            print(f"Database commit failed: {commit_error}")
            print(traceback.format_exc())
            db.rollback()
            print("Session rolled back due to commit failure")

        end_time = time.time()
        print(end_time - start_time)

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": content,
            "feedback": result["response"],
            "rag_id": result["rag_id"],
            "saved_to_db": bool(user_id),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_note(
    file: UploadFile = File(...),
    title: str = Form(...),
    subjects_id: str = Form(...),
    db: Session = Depends(deps.get_db),
    user_id: Optional[str] = Form(...),
):
    try:
        note_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        UPLOAD_DIR = "./uploads"
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        # 파일 내용 읽기
        content = await file.read()

        # 파일 확장자 확인 및 저장
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        # 파일 저장
        with open(file_path, "wb") as f:
            f.write(content)

        # 파일 포인터를 처음으로 되돌립니다
        await file.seek(0)

        # OCR 수행
        raw_text = await perform_ocr(file)

        # 노트 저장
        if user_id:
            note = Note(
                note_id=note_id,
                user_id=user_id,
                subjects_id=subjects_id,
                title=title,
                file_path=f"/{unique_filename}",
                raw_text=raw_text,
                cleaned_text=raw_text,
                ocr_yn="Y",
                del_yn="N",
            )
            db.add(note)
            db.commit()

        # RAG 분석 수행
        result = analysis_chunk(raw_text)
        print("Analysis Result:", result)

        # Note db subject 수정
        if subjects_id == "선택 안함":
            subjects_id = result["subjects_id"]
            note.subjects_id = subjects_id
            db.commit()

        # 분석 결과 저장
        if user_id:
            analysis = Analysis(
                analyze_id=str(uuid.uuid4())[:8],
                note_id=note_id,
                chunk_num=0,
                rag_id=result["rag_id"],
                feedback=result["response"],
            )
            db.add(analysis)
            db.commit()

        # O/X 퀴즈 생성
        quizzes = result.get("quiz", [])
        print("Quizzes:", quizzes)
        print("Type of quizzes:", type(quizzes))

        if isinstance(quizzes, str):
            try:
                quizzes = json.loads(quizzes)
                print("Quizzes after JSON parsing:", quizzes)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                quizzes = []

        if isinstance(quizzes, dict):
            quiz_list = quizzes.get("quiz", [])
        elif isinstance(quizzes, list):
            quiz_list = quizzes
        else:
            print(
                "Invalid structure of quizzes. Expected a string, dictionary, or list."
            )
            quiz_list = []

        for quiz in quiz_list:
            print("Processing quiz:", quiz)
            if not isinstance(quiz, dict):
                try:
                    quiz = ast.literal_eval(quiz)
                except (ValueError, SyntaxError) as e:
                    print(f"Error parsing quiz: {quiz} - {e}")
                    continue

            try:
                ox_id = str(uuid.uuid4())[:8]
                ox = OX(
                    ox_id=ox_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get("rag_id"),
                    ox_contents=quiz["question"],
                    ox_answer=quiz["answer"],
                    ox_explanation=quiz["explanation"],
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(ox)
                print(f"Successfully added OX with ox_id={ox_id} to session")
            except Exception as e:
                print(f"Error saving quiz: {e}")
                print(traceback.format_exc())
                continue

        # 객관식 퀴즈 생성 및 저장
        multiple_quizzes = result.get("multiple", [])
        print("Multiple Choice Quizzes:", multiple_quizzes)
        print("Type of multiple quizzes:", type(multiple_quizzes))

        if isinstance(multiple_quizzes, str):
            try:
                multiple_quizzes = json.loads(multiple_quizzes)
                print("Multiple quizzes after JSON parsing:", multiple_quizzes)
            except json.JSONDecodeError as e:
                print(f"Error decoding multiple JSON: {e}")
                multiple_quizzes = []

        multiple_list = []
        if isinstance(multiple_quizzes, dict):
            multiple_list = multiple_quizzes.get("questions", [])
        elif isinstance(multiple_quizzes, list):
            multiple_list = multiple_quizzes

        for quiz in multiple_list:
            print("Processing multiple quiz:", quiz)
            try:
                quiz_id = str(uuid.uuid4())[:8]
                multiple = MultipleChoice(
                    quiz_id=quiz_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get("rag_id"),
                    quiz_contents=quiz["question"],
                    option1=quiz["option1"],
                    option2=quiz["option2"],
                    option3=quiz["option3"],
                    option4=quiz["option4"],
                    quiz_answer=quiz["answer"],
                    quiz_explanation=quiz["explanation"],
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(multiple)
                print(f"Successfully added multiple choice quiz with quiz_id={quiz_id}")
            except Exception as e:
                print(f"Error saving multiple quiz: {e}")
                print(traceback.format_exc())
                continue

        # 커밋 실행
        try:
            print("Attempting to commit changes to the database...")
            db.commit()
            print("Database commit successful!")
        except Exception as commit_error:
            print(f"Database commit failed: {commit_error}")
            print(traceback.format_exc())
            db.rollback()
            print("Session rolled back due to commit failure")

        end_time = time.time()
        print(end_time - start_time)
        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "feedback": result["response"],
            "rag_id": result["rag_id"],
            "saved_to_db": bool(user_id),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def get_user_notes(
    user_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    subject: Optional[str] = None,
    sort: Optional[str] = "newest",
    db: Session = Depends(deps.get_db),
):
    try:
        query = (
            db.query(Note, Analysis)
            .outerjoin(Analysis, Note.note_id == Analysis.note_id)
            .filter(Note.user_id == user_id)
            .filter(Note.del_yn == "N")
        )

        if start_date:
            query = query.filter(Note.created_at >= start_date)
        if end_date:
            query = query.filter(Note.created_at <= end_date)
        if subject:
            query = query.filter(Note.subjects_id == subject)

        query = query.order_by(
            Note.created_at.desc() if sort == "newest" else Note.created_at.asc()
        )

        notes = query.all()

        return {
            "notes": [
                {
                    "note_id": note.Note.note_id,
                    "title": note.Note.title,
                    "raw_text": note.Note.raw_text,
                    "note_date": note.Note.created_at,
                    "is_analysis": note.Note.ocr_yn,
                    "feedback": note.Analysis.feedback if note.Analysis else None,
                    "subjects_id": note.Note.subjects_id,  # 과목 정보 추가
                }
                for note in notes
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
def get_note_detail(note_id: str, user_id: str, db: Session = Depends(deps.get_db)):
    try:
        result = (
            db.query(Note, Analysis)
            .outerjoin(Analysis, Note.note_id == Analysis.note_id)
            .filter(Note.note_id == note_id)
            .filter(Note.user_id == user_id)
            .filter(Note.del_yn == "N")
            .first()
        )

        if not result:
            raise HTTPException(status_code=404, detail="Note not found")

        note, analysis = result

        # 이미지 파일의 실제 파일 경로 확인
        file_path = None
        if note.ocr_yn == "Y" and note.file_path:
            file_path = os.path.join(os.getcwd(), note.file_path.lstrip("/"))

        return {
            "note_id": note.note_id,
            "title": note.title,
            "file_path": file_path,
            "raw_text": note.raw_text,
            "cleaned_text": note.cleaned_text,
            "note_date": note.created_at,
            "is_analysis": note.ocr_yn,
            "subjects_id": note.subjects_id,
            "feedback": analysis.feedback if analysis else None,
            "rag_id": analysis.rag_id if analysis else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/uploads")
def get_image(note_id: str, user_id: str, db: Session = Depends(deps.get_db)):
    try:
        # 노트와 분석 결과를 함께 조회
        result = (
            db.query(Note, Analysis)
            .outerjoin(Analysis, Note.note_id == Analysis.note_id)
            .filter(Note.note_id == note_id)
            .filter(Note.user_id == user_id)
            .filter(Note.del_yn == "N")
            .first()
        )

        if not result:
            raise HTTPException(status_code=404, detail="Note not found")

        note, analysis = result

        if note.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this note"
            )

        current_dir = os.path.dirname(__file__)
        print(current_dir.split("app")[0])

        # file_path = note.file_path
        file_path = current_dir.split("app")[0][:-1] + note.file_path
        print(file_path)
        return FileResponse(file_path)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count/{user_id}")
def get_notes_count(user_id: str, db: Session = Depends(deps.get_db)):
    result = (
        db.query(Note.subjects_id, func.count().label("count"))
        .filter(Note.user_id == user_id, Note.del_yn == "N")
        .group_by(Note.subjects_id)
        .all()
    )

    return {
        "counts": [
            {"subjects_id": row.subjects_id, "count": row.count} for row in result
        ]
    }


@router.get("/subjects")
def get_subjects(user_id: str, db: Session = Depends(deps.get_db)):
    subjects = (
        db.query(Note.subjects_id)
        .distinct()
        .filter(Note.user_id == user_id, Note.del_yn == "N")
        .all()
    )
    return {"subjects": [subject[0] for subject in subjects if subject[0]]}


@router.get("/activate-log/{user_id}")
def get_activate_log(user_id: str, db: Session = Depends(deps.get_db)):
    today = date.today()
    start_date = today - timedelta(days=363)

    query = text(
        """
    WITH RECURSIVE date_series AS (
        SELECT :start_date AS date
        UNION ALL
        SELECT date + INTERVAL 1 DAY
        FROM date_series
        WHERE date < :today
    )
    SELECT COALESCE(COUNT(n.created_at), 0) AS count
    FROM date_series ds
    LEFT JOIN tb_note n 
        ON DATE(n.created_at) = ds.date 
        AND n.user_id = :user_id
    GROUP BY ds.date
    ORDER BY ds.date;
    """
    )

    result = db.execute(
        query, {"start_date": start_date, "today": today, "user_id": user_id}
    )
    counts = [row[0] for row in result.fetchall()]

    return counts
