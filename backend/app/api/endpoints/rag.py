import uuid

from app.api import deps
from app.models.analysis import Analysis
from app.models.note import Note
from app.services.rag_service import analysis_chunk, create_vectorstore
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

        # result = analysis_note(note.contents)
        result = analysis_chunk(note.contents)
        print(result)

        # todo: DB에 결과 저장
        analyze_id = str(uuid.uuid4())[:8]
        analysis = Analysis(
            analyze_id=analyze_id,
            note_id=note_id,
            chunk_num=0,
            rag_id=result["rag_id"],
            field2=result["response"],
        )
        db.add(analysis)
        db.commit()

        return {
            "user_id": user_id,
            "note_id": note.note_id,
            "text": note.contents,
            "llm_result": result["response"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
