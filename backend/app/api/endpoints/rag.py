from app.api import deps
from app.models.note import Note
from app.services.rag_service import analysis_note, create_vectorstore
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

router = APIRouter()


class NoteInput(BaseModel):
    text: str


class VectorStoreInput(BaseModel):
    file_path: str


@router.post("/vectorstore")
async def post_create_vectorstore(input_data: VectorStoreInput):
    try:
        print(f"input data: {input_data}")
        print(input_data.file_path)

        result = create_vectorstore(input_data.file_path)
        print(result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def create_analysis_note(user_id: str, note_id: str, db: Session = Depends(deps.get_db)):
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

        result = analysis_note(note.contents)
        print(result)

        # todo: DB에 결과 저장

        return {
            "user_id": user_id,
            "note_id": note.note_id,
            "text": note.contents,
            "llm_result": note.contents_ocr,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
