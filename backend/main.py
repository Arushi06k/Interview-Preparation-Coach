# backend/main.py

# 1. Import all the necessary tools from FastAPI and other libraries.
from feedback import generate_feedback
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
import fitz, docx, io
import time
import logging
from pathlib import Path
import json
# Local modules / project files
import sql_models
import models
from database import SessionLocal, engine
from resume_parser import get_ranked_domains
from question_bank_handler import load_questions_from_file, select_questions, get_next_question

# NLP evaluation engine (your provided engine file)
# Ensure the file is placed as backend/nlp_evaluation_engine.py or adjust the import
from nlp_evaluation_engine import init_models as nlp_init_models, evaluate_answer as nlp_evaluate_answer

# This line creates the database file and tables if they don't exist.
sql_models.Base.metadata.create_all(bind=engine)

# App + logger
app = FastAPI(title="Interview Coach API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# ========= STARTUP: load question bank + initialize NLP models =========
@app.on_event("startup")
def on_startup():
    # Load question bank into memory
    try:
        load_questions_from_file()
        logger.info("Question bank loaded.")
    except Exception as e:
        logger.exception("Failed to load question bank: %s", e)
        # Not failing startup — but you can choose to raise if you want fail-fast.

    # Initialize heavy NLP models (from your engine)
    try:
        nlp_init_models()
        logger.info("NLP models initialized.")
    except Exception as e:
        logger.exception("Failed to init NLP models at startup: %s", e)
        # Re-raise if you prefer to fail fast:
        # raise

# Dependency: This function provides a database session for each API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def map_scores_for_feedback(details):
    # Convert NLP (0–1) metrics into 0–3 rubric scale
    accuracy = round(details.get("similarity", 0) * 3, 2)
    relevance = round(details.get("keyword_match", 0) * 3, 2)
    clarity = round(details.get("clarity", 0) * 3, 2)
    depth = round(details.get("length_score", 0) * 3, 2)

    return {
        "accuracy": accuracy,
        "depth": depth,
        "clarity": clarity,
        "relevance": relevance
    }

def normalize(value):
    """
    Normalizes ANY incoming score into a 0–10 scale.
    Handles:
        - 0–1 scores → converted to 0–10
        - 0–10 scores → kept as-is
        - 10–100 → treated as percentage → scaled down (÷10)
        - >100 → forced to 10
        - negative → forced to 0
    """
    try:
        v = float(value)
    except:
        return 0.0

    # Case: 0–1 → scale to 0–10
    if 0 <= v <= 1:
        return round(v * 10, 2)

    # Case: 1–10 → already correct
    if 1 < v <= 10:
        return round(v, 2)

    # Case: 10–100 → assume percentage
    if 10 < v <= 100:
        return round(v / 10, 2)

    # Garbage values above 100
    if v > 100:
        return 10.0

    # Negative values
    return 0.0


# --- Resume Analysis Endpoint ---
@app.post("/api/get-domains", response_model=models.DomainResponse, tags=["Resume Processing"])
async def get_domains_from_resume(resume: UploadFile = File(...)):
    allowed_mimetypes = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if resume.content_type not in allowed_mimetypes:
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: pdf, docx")

    try:
        file_stream = io.BytesIO(await resume.read())

        if resume.content_type == "application/pdf":
            extracted_text = "".join([page.get_text() for page in fitz.open(stream=file_stream, filetype="pdf")])
        else:
            extracted_text = "\n".join([p.text for p in docx.Document(file_stream).paragraphs])

        top_domains_data = get_ranked_domains(extracted_text)

        return {
            "filename": resume.filename,
            "top_domains": top_domains_data
        }
    except Exception as e:
        logger.exception("Resume processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Interview Session Endpoint ---
@app.post("/api/sessions", response_model=models.SessionResponse, tags=["Interview Sessions"])
def create_interview_session(
    session_data: models.SessionCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a new interview session and stores it in the database.
    """
    new_session = sql_models.InterviewSession(
        selected_domain=session_data.selected_domain,
        difficulty_level=session_data.difficulty_level,
        resume_analysis_result=session_data.resume_analysis_result.model_dump()
    )

    # Ensure generated_questions and interview_results are initialized as empty lists
    new_session.generated_questions = [] if new_session.generated_questions is None else new_session.generated_questions
    new_session.interview_results = [] if new_session.interview_results is None else new_session.interview_results

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session

# --- Generate questions for a session (phase 2) ---
@app.post("/api/sessions/{session_id}/generate-questions", tags=["Interview Sessions"])
def generate_interview_questions(session_id: int, db: Session = Depends(get_db)):
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # select_questions returns {"questions": [...], "meta": {...}}
        selection = select_questions(
            domain=session.selected_domain,
            difficulty=session.difficulty_level,
            num_questions=10
        )

        selected_questions = selection.get("questions", [])

        if not selected_questions:
            raise HTTPException(
                status_code=404,
                detail=f"No questions found for domain '{session.selected_domain}' and difficulty '{session.difficulty_level}'."
            )

        # Save only the actual questions list
        session.generated_questions = selected_questions
        session.interview_results = session.interview_results or []

        db.commit()
        db.refresh(session)

        # And return a clean structure
        return {
            "session_id": session_id,
            "questions": selected_questions
        }

    except Exception as e:
        db.rollback()
        logger.exception("Error generating questions: %s", e)
        raise HTTPException(status_code=500, detail=f"Error generating questions: {str(e)}")


# ---------------------- Helper: determine next question respecting answered questions ----------------------
def _get_next_unanswered_question(session_obj):
    """
    Determine the next question from session.generated_questions that has not been answered yet.
    We assume questions have unique 'id' or unique 'question' text.
    This function reads session.interview_results and checks for 'raw' or 'evaluated' entries.
    """
    generated = session_obj.generated_questions or []
    answered_questions = set()
    for entry in (session_obj.interview_results or []):
        if not isinstance(entry, dict):
            continue
        # raw or evaluated entries store "question" key
        qtext = entry.get("question")
        if qtext:
            answered_questions.add(qtext.strip())

    for q in generated:
        qtext = q.get("question") if isinstance(q, dict) else None
        # fallback to string if generated question is a plain string
        if not qtext:
            qtext = str(q).strip()
        if qtext and qtext not in answered_questions:
            return q
    return None

# --- Sequential Question Flow: get next question based on answered questions ---
@app.post("/api/sessions/{session_id}/next-question", tags=["Interview Sessions"])
def next_question(session_id: int, payload: dict, db: Session = Depends(get_db)):
    """
    Returns the next question in sequence using simple answered-question tracking.
    payload = { "current_question": {...} }  -- current_question optional
    """
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session or not session.generated_questions:
        raise HTTPException(status_code=404, detail="No questions found for this session. Generate questions first.")

    # If client passes current_question, we trust it but still compute next based on stored answers.
    next_q = _get_next_unanswered_question(session)
    if not next_q:
        return {"message": "No more questions."}

    return next_q

# ---------------------- Save raw user answer (no evaluation) ----------------------
@app.post("/api/sessions/{session_id}/save-answer", tags=["Interview Sessions"])
def save_user_answer(session_id: int, payload: dict, db: Session = Depends(get_db)):
    """
    Saves the user's raw answer (no evaluation).
    payload = {"question": "What is AI?", "answer": "Artificial intelligence is..."}
    We tag entries with "type": "raw" so they can be bulk-evaluated later.
    """
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        entry = {
            "type": "raw",
            "question": payload.get("question", ""),
            "answer": payload.get("answer", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        current_results = session.interview_results or []
        current_results.append(entry)
        session.interview_results = current_results

        db.commit()
        db.refresh(session)

        return {"message": "✅ Answer saved successfully!", "entry": entry}

    except Exception as e:
        db.rollback()
        logger.exception("save_user_answer failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------- Evaluate single answer (existing endpoint) ----------------------
@app.post("/api/sessions/{session_id}/evaluate-answer", tags=["Interview Sessions"])
def evaluate_answer(session_id: int, payload: models.AnswerPayload, db: Session = Depends(get_db)):
    """
    Evaluates a user's answer and saves the result to the database.
    This endpoint evaluates a single provided answer immediately and tags it as 'evaluated'.
    """
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        # Fetch full question object from session.generated_questions
        matched_q = next((q for q in (session.generated_questions or []) 
                  if q.get("question") == payload.question), None)

        if not matched_q:
           raise HTTPException(status_code=400, detail="Question not found in session.")

        # NOTE: benchmark_answer should actually be the model/expected answer text if available.
        benchmark_answer = matched_q.get("expected_answer", matched_q.get("question", ""))
        keywords = matched_q.get("keywords_str", "").split(",") if matched_q.get("keywords_str") else []

        # Call NLP engine
        result = nlp_evaluate_answer(
            user_answer=payload.answer,
            benchmark_answer=benchmark_answer,
            question_keywords=keywords
        ) or {}

        # --- Normalize raw engine score (be defensive about key naming) ---
        # engine might return 'final_score' (0-100), 'score' (0-10), or 'final' etc.
        raw_score = None
        for k in ("final_score", "score", "final", "raw_score"):
            if k in result:
                try:
                    raw_score = float(result[k])
                    break
                except Exception:
                    raw_score = None

        # If engine didn't return a single final number, try to compute one from components
        if raw_score is None:
            # try common components (0-1)
            sim = float(result.get("similarity_score", result.get("similarity", 0))) or 0.0
            kw = float(result.get("keyword_score", result.get("keyword_match", 0))) or 0.0
            clarity = float(result.get("clarity", 0)) or 0.0

            # length_score fallback: small heuristic
            wc = len((payload.answer or "").split())
            if wc < 8:
                length_score = 0.1
            elif wc < 15:
                length_score = 0.4
            elif wc < 25:
                length_score = 0.7
            elif wc < 60:
                length_score = 1.0
            else:
                length_score = 0.6

            weighted_sum = sim * 0.40 + kw * 0.25 + length_score * 0.20 + clarity * 0.15
            raw_score = round(weighted_sum * 100, 2)  # convert to 0-100 style so normalize will handle it
        # Now normalize the raw_score into 0-10 using your normalize()
        score = normalize(raw_score)

        # Build a canonical details dict (0-1 for components where possible)
        canonical_details = {
            "similarity": float(result.get("similarity_score", result.get("similarity", 0))) or 0.0,
            "clarity": float(result.get("clarity", 0)) or 0.0,
            "keyword_match": float(result.get("keyword_score", result.get("keyword_match", 0))) or 0.0,
            # Keep engine's final raw numeric under details as well for traceability:
            "engine_raw_score": raw_score,
            # include any other engine-provided parts verbatim (non-normalized)
            "engine_extra": {k: v for k, v in result.items() if k not in ("similarity_score", "similarity", "clarity", "keyword_score", "keyword_match", "final_score", "score", "raw_score")}
        }

        evaluation_result = {
            "type": "evaluated",
            "question": payload.question,
            "answer": payload.answer,
            "score": score,
            "raw_score": raw_score,
            "details": canonical_details,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        # Append to interview_results
        current_results = session.interview_results or []
        current_results.append(evaluation_result)
        session.interview_results = current_results

        db.commit()
        db.refresh(session)

        return evaluation_result

    except Exception as e:
        db.rollback()
        logger.exception("evaluate_answer failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------- Evaluate All Raw Answers (bulk evaluation) ----------------------
@app.post("/api/sessions/{session_id}/evaluate-all", tags=["Interview Sessions"])
def evaluate_all(session_id: int, db: Session = Depends(get_db)):
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        all_results = session.interview_results or []
        raw_entries = [r for r in all_results if r.get("type") == "raw"]

        if not raw_entries:
            return {"message": "No raw answers to evaluate.", "evaluations": []}

        evaluations = []

        for raw in raw_entries:
            question_text = raw.get("question", "")
            user_answer = raw.get("answer", "")

            # Extract benchmark + keywords
            benchmark_answer = ""
            question_keywords = []

            for q in (session.generated_questions or []):
                if q.get("question") == question_text:
                    benchmark_answer = q.get("question", "")
                    question_keywords = q.get("keywords_str", "").split(",")
                    break

            # -------- NLP ENGINE RAW OUTPUT --------
            eval_result = nlp_evaluate_answer(
                user_answer=user_answer,
                benchmark_answer=benchmark_answer,
                question_keywords=question_keywords
            )

            # Extract NLP Components
            sim = float(eval_result.get("similarity_score", 0))  # 0–1
            relevance = float(eval_result.get("relevance", 0))    # 0–1
            clarity = float(eval_result.get("clarity", 0))        # 0–1
            keyword_match = float(eval_result.get("keyword_score", 0))  # 0–1

            # -------- Length Score (0–1) --------
            wc = len(user_answer.split())
            if wc < 8:
                length_score = 0.1
            elif wc < 15:
                length_score = 0.4
            elif wc < 25:
                length_score = 0.7
            elif wc < 60:
                length_score = 1.0
            else:
                length_score = 0.6  # too long, reduce score

            # -------- Final Weighted Score (0–10) --------
            weighted_sum = (
                sim * 0.40 +
                keyword_match * 0.25 +
                length_score * 0.20 +
                clarity * 0.15
            )

            # Theoretical max (1 * each weight)
            max_possible = 0.40 + 0.25 + 0.20 + 0.15  # = 1.0 exactly

            normalized = weighted_sum / max_possible   # always 0–1
            final_score = round(normalized * 10, 2)    # convert to 0–10


            # -------- Custom Human-like Feedback --------
            feedback_parts = []
            if final_score >= 8:
                feedback_parts.append("Very strong answer. You covered key points with clarity and depth.")
            elif final_score >= 6:
                feedback_parts.append("Good answer, but you can increase depth and provide real examples.")
            elif final_score >= 4:
                feedback_parts.append("Average answer. Add more structure and include relevant concepts.")
            else:
                feedback_parts.append("Weak response. Revise fundamentals and give more elaborate explanations.")

            if keyword_match < 0.4:
                feedback_parts.append("You missed several important keywords from the expected answer.")

            if clarity < 0.5:
                feedback_parts.append("Your explanation lacked clarity or proper flow.")

            if length_score < 0.3:
                feedback_parts.append("Your answer was too short. Add more explanation.")

            final_feedback = " ".join(feedback_parts)

            evaluated_entry = {
                "type": "evaluated",
                "question": question_text,
                "answer": user_answer,
                "score": final_score,
                "details": {
                    "similarity": sim,
                    "clarity": clarity,
                    "keyword_match": keyword_match,
                    "length_score": length_score,
                    "feedback": final_feedback
                },
                "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%S")
            }

            all_results.append(evaluated_entry)
            evaluations.append(evaluated_entry)

        # Save
        session.interview_results = all_results
        db.commit()
        db.refresh(session)

        return {"message": f"Evaluated {len(evaluations)} answers.", "evaluations": evaluations}

    except Exception as e:
        db.rollback()
        raise


# ---------------------- Final Results Endpoint for Module 5 ----------------------
@app.get("/api/sessions/{session_id}/results", tags=["Interview Sessions"])
def get_session_results(session_id: int, db: Session = Depends(get_db)):
    session = db.query(sql_models.InterviewSession).filter(sql_models.InterviewSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    evaluated = [
        r for r in (session.interview_results or [])
        if isinstance(r, dict) and r.get("type") == "evaluated"
    ]

    to_feedback_engine = []
    for e in evaluated:
        normalized_score = normalize(e.get("score", 0))  # ← only this is needed

        to_feedback_engine.append({
            "question": e["question"],
            "score": normalized_score,
            "reason": e["details"].get("feedback", "No feedback."),
            "criteria": map_scores_for_feedback(e["details"]),
            "answer": e.get("answer", "Not provided")
        })


    final_feedback = generate_feedback(to_feedback_engine)

    # Merge user answer into evaluations
    for fe, e in zip(final_feedback["evaluations"], evaluated):
        fe["your_answer"] = e.get("answer", "Not provided")

    return final_feedback
