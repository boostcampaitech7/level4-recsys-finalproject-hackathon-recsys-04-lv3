# models/rag.py
from sqlalchemy import Column, String
from app.db.base import TimeStampedBase

class RAG(TimeStampedBase):
    __tablename__ = "tb_rag"
    
    rag_id = Column(String(10), primary_key=True, comment='유니크한 RAG 아이디')
    subjects_id = Column(String(10), nullable=False, comment='과목 아이디 코드')
    field = Column(String(200), nullable=True)