from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from app.db.base import TimeStampedBase


class Note(TimeStampedBase):
    __tablename__ = "tb_note"

    note_id = Column(String(10), primary_key=True, comment="유니크한 노트 아이디")
    user_id = Column(
        String(10),
        ForeignKey("tb_user.user_id"),
        nullable=False,
        comment="노트를 생성한 유저 아이디",
    )
    subjects_id = Column(String(10), nullable=True, comment="과목")
    file_path = Column(String(200), nullable=True, comment="업로드한 파일 경로")
    title = Column(String(200), nullable=True, comment="제목")
    raw_text = Column(Text, nullable=True, comment="원본 텍스트")
    cleaned_text = Column(Text, nullable=True, comment="정제된 텍스트")
    ocr_yn = Column(String(1), nullable=False, default="N", comment="본문 완료 여부")
    del_yn = Column(String(1), nullable=False, default="N", comment="노트 삭제 여부")
