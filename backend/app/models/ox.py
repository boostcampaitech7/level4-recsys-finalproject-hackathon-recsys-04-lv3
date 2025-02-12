# models/ox.py
from sqlalchemy import Column, String, ForeignKey
from app.db.base import TimeStampedBase


class OX(TimeStampedBase):
    __tablename__ = "tb_ox"

    ox_id = Column(String(10), primary_key=True, comment="유니크한 ox 퀴즈 아이디")
    user_id = Column(
        String(10),
        ForeignKey("tb_user.user_id"),
        nullable=False,
        comment="대상 유저 아이디",
    )
    note_id = Column(
        String(10),
        ForeignKey("tb_note.note_id"),
        nullable=False,
        comment="대상 노트 아이디",
    )
    rag_id = Column(String(300), nullable=False, comment="관련 RAG 아이디")
    ox_contents = Column(String(200), nullable=False, comment="퀴즈 문제 본문")
    ox_answer = Column(String(1), nullable=False, comment='해당 퀴즈의 정답("O"/"X")')
    ox_explanation = Column(String(200), nullable=True, comment="퀴즈의 정답 설명")
    used_yn = Column(
        String(1), nullable=False, default="N", comment='문제 풀 여부("Y"/"N")'
    )
    correct_yn = Column(
        String(1), nullable=False, default="N", comment='정답 여부("Y"/"N")'
    )
    del_yn = Column(
        String(1), nullable=False, default="N", comment='삭제 여부("Y"/"N")'
    )
