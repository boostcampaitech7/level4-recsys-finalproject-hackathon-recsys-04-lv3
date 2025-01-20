# models/code.py
from sqlalchemy import Column, String
from app.db.base import TimeStampedBase

class Code(TimeStampedBase):
    __tablename__ = "tb_code"
    
    code_id = Column(String(10), primary_key=True, comment='유니크한 코드 아이디')
    upper_code_id = Column(String(10), nullable=True, comment='상위 코드 아이디')
    tag = Column(String(200), nullable=True, comment='코드 용도 설명')
    del_yn = Column(String(1), nullable=False, default='N', comment='삭제 여부("Y"/"N")')