from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Body
from sqlalchemy.orm import Session 
from typing import Optional
from app.api import deps
from app.models.note import Note
from app.services import ocr
from app.services.rag_service import RAGService
import uuid
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

class TextNote(BaseModel):
   title: str
   subjects_id: str 
   content: str

@router.post("/text")
async def create_text_note(
   text_note: TextNote,
   db: Session = Depends(deps.get_db),
   user_id: Optional[str] = None
):
   try:
       note_id = str(uuid.uuid4())[:8]
       
       # RAG 서비스 초기화
       rag_service = RAGService()
       
       # 기본 피드백과 RAG 피드백 생성
       basic_feedback, rag_feedback = await rag_service.generate_feedback(text_note.content)
       
       if user_id:
           note = Note(
               note_id=note_id,
               user_id=user_id,
               subjects_id=text_note.subjects_id,
               title=text_note.title,
               contents=text_note.content,
               ocr_yn='N',
               del_yn='N'
           )
           db.add(note)
           db.commit()
       
       return {
           "note_id": note_id if user_id else None,
           "content": text_note.content,
           "basic_feedback": basic_feedback,
           "rag_feedback": rag_feedback,
           "saved_to_db": bool(user_id)
       }
       
   except Exception as e:
       db.rollback()
       raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload")
async def upload_note(
   file: UploadFile,
   title: str,
   subjects_id: str, 
   db: Session = Depends(deps.get_db),
   user_id: Optional[str] = None
):
   try:
       # OCR로 텍스트 추출
       raw_text = await ocr.perform_ocr(file)
       note_id = str(uuid.uuid4())[:8]
       
       # RAG 서비스 초기화
       rag_service = RAGService()
       
       # 기본 피드백과 RAG 피드백 생성
       basic_feedback, rag_feedback = await rag_service.generate_feedback(raw_text)
       
       if user_id:
           note = Note(
               note_id=note_id,
               user_id=user_id,
               subjects_id=subjects_id,
               title=title,
               file_path=f"uploads/{file.filename}",
               contents=raw_text,
               contents_ocr=raw_text,
               ocr_yn='Y',
               del_yn='N'
           )
           db.add(note)
           db.commit()
       
       return {
           "note_id": note_id if user_id else None,
           "raw_text": raw_text,
           "basic_feedback": basic_feedback, 
           "rag_feedback": rag_feedback,
           "saved_to_db": bool(user_id)
       }
       
   except Exception as e:
       db.rollback()
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/my-notes")
def get_user_notes(user_id: str, db: Session = Depends(deps.get_db)):
   try:
       notes = db.query(Note)\
           .filter(Note.user_id == user_id)\
           .filter(Note.del_yn == 'N')\
           .all()
       
       return {
           "notes": [
               {
                   "note_id": note.note_id,
                   "title": note.title,
                   "raw_text": note.contents,
                   "note_date": note.created_at,
                   "is_analysis": note.ocr_yn
               }
               for note in notes
           ]
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{note_id}")
def get_note_detail(
   note_id: str,
   user_id: str,
   db: Session = Depends(deps.get_db)
):
   try:
       note = db.query(Note)\
           .filter(Note.note_id == note_id)\
           .filter(Note.del_yn == 'N')\
           .first()
       
       if not note:
           raise HTTPException(status_code=404, detail="Note not found")
       if note.user_id != user_id:
           raise HTTPException(status_code=403, detail="Not authorized to access this note")
       
       return {
           "note_id": note.note_id,
           "title": note.title,
           "raw_text": note.contents,
           "cleaned_text": note.contents_ocr,
           "note_date": note.created_at,
           "is_analysis": note.ocr_yn,
           "subjects_id": note.subjects_id
       }
       
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))