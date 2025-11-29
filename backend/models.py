from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ----------------------------------------------------------
# 🧾 Models for Resume Analysis
# ----------------------------------------------------------
class DomainInfo(BaseModel):
    domain_name: str
    skills_found: List[str]

class DomainResponse(BaseModel):
    filename: str
    top_domains: List[DomainInfo]

# ----------------------------------------------------------
# 🎯 Models for Interview Sessions
# ----------------------------------------------------------
class SessionCreate(BaseModel):
    """The data sent by frontend to create a session."""
    selected_domain: str
    difficulty_level: str
    resume_analysis_result: DomainResponse = Field(...)

class SessionResponse(BaseModel):
    """Response returned after creating a session."""
    id: int
    user_id: Optional[str] = None
    selected_domain: str
    difficulty_level: str
    session_date: datetime

    class Config:
        from_attributes = True  # enables direct mapping from SQLAlchemy models

# ----------------------------------------------------------
# 🧠 NEW FOR PHASE 4 — Answer Evaluation
# ----------------------------------------------------------
class AnswerPayload(BaseModel):
    """
    Defines the structure for question and answer sent from frontend
    during answer evaluation.
    """
    question: str
    answer: str

    # Optional additional fields for AI evaluation
    benchmark: Optional[str] = Field(
        default=None,
        description="Reference (ideal) answer for semantic comparison."
    )
    keywords: Optional[List[str]] = Field(
        default=None,
        description="List of domain-specific keywords expected in the answer."
    )

# ----------------------------------------------------------
# 📊 Optional: Model for returning evaluation results
# ----------------------------------------------------------
class EvaluationResult(BaseModel):
    question: str
    answer: str
    evaluation: Dict[str, Any]

# ----------------------------------------------------------
# 🏁 Optional: Wrapper for final results (Module 5)
# ----------------------------------------------------------
class SessionResults(BaseModel):
    session_id: int
    selected_domain: str
    difficulty_level: str
    results: List[EvaluationResult]
