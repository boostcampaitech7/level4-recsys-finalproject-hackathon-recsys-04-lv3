# models/feedback.py
from sqlalchemy import Column, String, ForeignKey
from app.db.base import TimeStampedBase

class Feedback(TimeStampedBase):
    __tablename__ = "tb_feedback"
    
    feedback_id = Column(String(10), primary_key=True, comment='유니크한 피드백 아이디')
    analyze_id = Column(String(10), ForeignKey("tb_analyze.analyze_id"), nullable=True, comment='분석 아이디')