from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.mutable import MutableList   # ✅ ADD THIS
from database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, default="default_user")
    selected_domain = Column(String, index=True)
    difficulty_level = Column(String)
    session_date = Column(DateTime(timezone=True), server_default=func.now())
    resume_analysis_result = Column(JSON)

    # Store generated questions
    generated_questions = Column(MutableList.as_mutable(JSON), nullable=True)   # ✅ FIXED

    # Store ALL answers (multiple entries)
    interview_results = Column(MutableList.as_mutable(JSON), nullable=True)    # ✅ FIXED
