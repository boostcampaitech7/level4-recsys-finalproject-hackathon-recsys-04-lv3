# app/models/document.py
from sqlalchemy import Column, String, Integer, ARRAY, Float
from ..db.base_class import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    embedding = Column(ARRAY(Float))  # 임베딩 벡터 저장
    source = Column(String)  # 원본 문서 파일명