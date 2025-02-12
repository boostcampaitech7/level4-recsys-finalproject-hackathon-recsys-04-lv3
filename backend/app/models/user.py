from sqlalchemy import Column, String, Boolean
from app.db.base import TimeStampedBase


class User(TimeStampedBase):
    __tablename__ = "tb_user"

    user_id = Column(String(10), primary_key=True, comment="유니크한 유저 아이디")
    email = Column(String(20), nullable=False, comment="아이디")
    password = Column(String(20), nullable=False, comment="비밀번호")
    del_yn = Column(String(1), nullable=False, default="N", comment="회원 탈퇴 여부")
