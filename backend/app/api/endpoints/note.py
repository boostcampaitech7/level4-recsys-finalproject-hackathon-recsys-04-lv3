import uuid
from typing import Optional

from app.api import deps
from app.models.note import Note
from app.services.ocr_service import perform_ocr
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

        if user_id:
            note = Note(
                note_id=note_id,
                user_id=user_id,
                subjects_id=subjects_id,
                title=title,
                contents=content,
                ocr_yn="N",
                del_yn="N",
            )
            db.add(note)
            db.commit()

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": content,
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
        # OCR로 텍스트 추출
        raw_text = await perform_ocr(file)
        note_id = str(uuid.uuid4())[:8]

        if user_id:
            note = Note(
                note_id=note_id,
                user_id=user_id,
                subjects_id=subjects_id,
                title=title,
                file_path=f"uploads/{file.filename}",
                contents=raw_text,
                contents_ocr=raw_text,
                ocr_yn="Y",
                del_yn="N",
            )
            db.add(note)
            db.commit()

        return {
            "note_id": note_id if user_id else None,
            "user_id": user_id,
            "subjects_id": subjects_id,
            "title": title,
            "content": raw_text,
            "saved_to_db": bool(user_id),
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
def get_user_notes(user_id: str, db: Session = Depends(deps.get_db)):
    try:
        notes = db.query(Note).filter(Note.user_id == user_id).filter(Note.del_yn == "N").all()

        return {
            "notes": [
                {
                    "note_id": note.note_id,
                    "title": note.title,
                    "raw_text": note.contents,
                    "note_date": note.created_at,
                    "is_analysis": note.ocr_yn,
                }
                for note in notes
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}")
def get_note_detail(note_id: str, user_id: str, db: Session = Depends(deps.get_db)):
    try:
        note = (
            db.query(Note)
            .filter(Note.note_id == note_id)
            .filter(Note.user_id == user_id)
            .filter(Note.del_yn == "N")
            .first()
        )

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
            "subjects_id": note.subjects_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
