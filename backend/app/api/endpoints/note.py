# app/api/endpoints/note.py
import ast
import os
import uuid
import time
import json
from typing import Optional

from app.api import deps
from app.models.analysis import Analysis
from app.models.note import Note
from app.models.ox import OX
from app.services.ocr_service import perform_ocr
from app.services.rag_service import analysis_chunk
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

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
        start_time=time.time()

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
        print("Analysis Result:", result)  # 디버깅용 로그

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

        quizzes = result.get('quiz', [])
        print("Quizzes:", quizzes)  # 디버깅용 로그
        print("Type of quizzes:", type(quizzes))  # quizzes의 타입 확인

        # 문자열인 경우 JSON 파싱 시도
        if isinstance(quizzes, str):
            try:
                quizzes = json.loads(quizzes)  # 문자열을 JSON 객체로 변환
                print("Quizzes after JSON parsing:", quizzes)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                quizzes = []  # 변환 실패 시 빈 리스트로 초기화

        # 딕셔너리인 경우 'quiz' 키에서 리스트 추출
        if isinstance(quizzes, dict):
            quiz_list = quizzes.get("quiz", [])
        # 리스트인 경우 그대로 사용
        elif isinstance(quizzes, list):
            quiz_list = quizzes
        # 그 외의 경우 처리 불가
        else:
            print("Invalid structure of quizzes. Expected a string, dictionary, or list.")
            quiz_list = []


        for quiz in quiz_list:
            print("Processing quiz:", quiz)  # quiz 내용 출력
            if not isinstance(quiz, dict):
                try:
                    import ast
                    quiz = ast.literal_eval(quiz)  # 문자열을 딕셔너리로 변환
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
                import traceback
                print(traceback.format_exc())
                continue
            
        # 커밋 실행
        try:
            print("Attempting to commit changes to the database...")
            db.commit()
            print("Database commit successful!")
        except Exception as commit_error:
            print(f"Database commit failed: {commit_error}")
            import traceback

            print(traceback.format_exc())
            db.rollback()
            print("Session rolled back due to commit failure")

        end_time = time.time()
        print(end_time-start_time)
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
        quizzes = result.get('quiz', [])
        print("Quizzes:", quizzes)  # 디버깅용 로그

        # quiz_list 처리
        quiz_list = []
        if isinstance(quizzes, dict):
            if "quiz" in quizzes:
                quiz_list = quizzes["quiz"]
            elif "quizzes" in quizzes:
                quiz_list = quizzes["quizzes"]
        elif isinstance(quizzes, list):
            quiz_list = quizzes

        if user_id:
            for quiz in quiz_list:
                print("Quiz:", quiz)  # quiz 출력
                print("Type of quiz:", type(quiz))  # quiz 타입 출력

                if isinstance(quiz, str):
                    quiz = ast.literal_eval(quiz)
                    print("Converted quiz:", quiz)

                ox_id = str(uuid.uuid4())[:8]
                ox = OX(
                    ox_id=ox_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result["rag_id"],
                    ox_contents=quiz["question"],
                    ox_answer=quiz["answer"],
                    ox_explanation=quiz["explanation"],
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(ox)
                print(f"Successfully added OX with ox_id={ox_id} to session")

            try:
                print("Attempting to commit changes to the database...")
                db.commit()
                print("Database commit successful!")
            except Exception as commit_error:
                print(f"Database commit failed: {commit_error}")
                import traceback

                print(traceback.format_exc())
                db.rollback()
                print("Session rolled back due to commit failure")

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": raw_text,
            "feedback": result["response"],
            "rag_id": result["rag_id"],
            "file_extension": file_extension,
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

        query = query.order_by(Note.created_at.desc() if sort == "newest" else Note.created_at.asc())

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
            raise HTTPException(status_code=403, detail="Not authorized to access this note")

        import os

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
    count = db.query(Note).filter(Note.user_id == user_id, Note.del_yn == "N").count()
    return {"count": count}


@router.get("/subjects")
def get_subjects(user_id: str, db: Session = Depends(deps.get_db)):
    subjects = db.query(Note.subjects_id).distinct().filter(Note.user_id == user_id, Note.del_yn == "N").all()
    return {"subjects": [subject[0] for subject in subjects if subject[0]]}
