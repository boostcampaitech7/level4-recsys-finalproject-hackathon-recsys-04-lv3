# app/api/endpoints/note.py
import uuid
from typing import Optional

from app.api import deps
from app.models.ox import OX
from app.models.note import Note
from app.models.analysis import Analysis
from app.services.ocr_service import perform_ocr
from app.services.rag_service import analysis_chunk
from app.services.quiz_service import generate_quiz
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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
        
        # 분석 결과 저장
        if user_id:
            analysis = Analysis(
                analyze_id=str(uuid.uuid4())[:8],
                note_id=note_id,
                chunk_num=0,
                rag_id=result["rag_id"],
                feedback=result["response"]
            )
            db.add(analysis)
            db.commit()

        # O/X 퀴즈 생성
        quizzes = await generate_quiz(content)  # 퀴즈 생성 요청

        # 'quiz' 키 내부의 리스트를 순회
        for quiz in quizzes:  # 'quiz' 키가 아니라 리스트 자체를 순회
            try:
                # quiz가 문자열일 경우 처리
                if isinstance(quiz, str):
                    ox_contents = quiz  # 문자열을 퀴즈 내용으로 사용
                    ox_answer = None  # 문자열인 경우에는 정답을 처리할 수 없으므로 None으로 설정
                    ox_explanation = None  # 설명도 없는 경우로 설정
                else:
                    # quiz가 딕셔너리일 경우
                    ox_contents = quiz["question"]
                    ox_answer = quiz["answer"]
                    ox_explanation = quiz.get("explanation", "")  # 설명이 없으면 빈 문자열로 처리
                ox_id = str(uuid.uuid4())[:8]
                ox = OX(
                    ox_id=ox_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get('rag_id'),
                    ox_contents=quiz["question"],  
                    ox_answer=quiz["answer"],     
                    ox_explanation=quiz["explanation"], 
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(ox)
                print(f"Successfully added OX with ox_id={ox_id} to session")  # 성공 로그
            
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

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": content,
            "feedback": result["response"],
            "rag_id": result["rag_id"],
            "saved_to_db": bool(user_id)
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
        # OCR 수행
        raw_text = await perform_ocr(file)
        note_id = str(uuid.uuid4())[:8]

        # 노트 저장
        if user_id:
            note = Note(
                note_id=note_id,
                user_id=user_id,
                subjects_id=subjects_id,
                title=title,
                file_path=f"uploads/{file.filename}",
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
                feedback=result["response"]
            )
            db.add(analysis)
            db.commit()
            
         # O/X 퀴즈 생성
        quizzes = await generate_quiz(raw_text)  # 퀴즈 생성 요청

        # 'quiz' 키 내부의 리스트를 순회
        for quiz in quizzes:  # 'quiz' 키가 아니라 리스트 자체를 순회
            # quiz가 문자열일 경우 처리
            if isinstance(quiz, str):
                ox_contents = quiz  # 문자열을 퀴즈 내용으로 사용
                ox_answer = None  # 문자열인 경우에는 정답을 처리할 수 없으므로 None으로 설정
                ox_explanation = None  # 설명도 없는 경우로 설정
            else:
                # quiz가 딕셔너리일 경우
                ox_contents = quiz["question"]
                ox_answer = quiz["answer"]
                ox_explanation = quiz.get("explanation", "")  # 설명이 없으면 빈 문자열로 처리
            try:
                ox_id = str(uuid.uuid4())[:8]
                ox = OX(
                    ox_id=ox_id,
                    user_id=user_id,
                    note_id=note_id,
                    rag_id=result.get('rag_id'),
                    ox_contents=quiz["question"],  
                    ox_answer=quiz["answer"],     
                    ox_explanation=quiz["explanation"], 
                    used_yn="N",
                    correct_yn="N",
                    del_yn="N",
                )
                db.add(ox)
                print(f"Successfully added OX with ox_id={ox_id} to session")  # 성공 로그
            
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
            

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": raw_text,
            "feedback": result["response"],
            "rag_id": result["rag_id"],
            "saved_to_db": bool(user_id)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
def get_user_notes(user_id: str, db: Session = Depends(deps.get_db)):
    try:
        notes = (
            db.query(Note, Analysis)
            .outerjoin(Analysis, Note.note_id == Analysis.note_id)
            .filter(Note.user_id == user_id)
            .filter(Note.del_yn == "N")
            .all()
        )

        return {
            "notes": [
                {
                    "note_id": note.Note.note_id,
                    "title": note.Note.title,
                    "raw_text": note.Note.raw_text,
                    "note_date": note.Note.created_at,
                    "is_analysis": note.Note.ocr_yn,
                    "feedback": note.Analysis.feedback if note.Analysis else None
                }
                for note in notes
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{note_id}")
def get_note_detail(note_id: str, user_id: str, db: Session = Depends(deps.get_db)):
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

        return {
            "note_id": note.note_id,
            "title": note.title,
            "raw_text": note.raw_text,
            "cleaned_text": note.cleaned_text,
            "note_date": note.created_at,
            "is_analysis": note.ocr_yn,
            "subjects_id": note.subjects_id,
            "feedback": analysis.feedback if analysis else None,
            "rag_id": analysis.rag_id if analysis else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))