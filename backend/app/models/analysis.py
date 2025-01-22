# models/analysis.py
from app.db.base import TimeStampedBase
from sqlalchemy import Column, ForeignKey, Integer, String


class Analysis(TimeStampedBase):
    __tablename__ = "tb_analyze"

    analyze_id = Column(String(10), primary_key=True, comment="분석 고유 아이디")
    note_id = Column(String(10), ForeignKey("tb_note.note_id"), nullable=True, comment="노트 아이디")
    chunk_num = Column(Integer, nullable=True, comment="청크 번호")
    rag_id = Column(String(64), nullable=True, comment="RAG 아이디")
    field2 = Column(String(200), nullable=True)
