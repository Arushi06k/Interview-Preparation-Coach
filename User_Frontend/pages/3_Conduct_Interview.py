import streamlit as st
import requests
import io
import base64
from gtts import gTTS
import json
from datetime import datetime
from pathlib import Path   # FIXED
import os

st.set_page_config(page_title="Conduct Interview", page_icon="🎙️")

BACKEND_HOST = st.session_state.get("BACKEND_HOST", "http://127.0.0.1:8080")

st.title("Interview in Progress... 🎙️")
st.markdown("**Voice Mode Active:** Click the record button to speak your answer or type below.**")

# -------------------------------------------
# SAFETY GUARD
# -------------------------------------------
if "session_id" not in st.session_state or "questions" not in st.session_state:
    st.warning("No active interview session. Please generate questions first.")
    st.page_link("pages/2_Question_Generation.py", label="Go to Question Generation", icon="✨")
    st.stop()

# -------------------------------------------
# STATE DEFAULTS
# -------------------------------------------
st.session_state.setdefault("current_question_index", 0)
st.session_state.setdefault("user_answers", [])
st.session_state.setdefault("transcribed_answer", "")

questions = st.session_state.questions
i = st.session_state.current_question_index


# -------------------------------------------
# UTILITIES
# -------------------------------------------
def autoplay_text(text: str):
    """Play text as TTS."""
    try:
        tts = gTTS(text=text, lang="en")
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        st.markdown(
            f"""
            <audio autoplay controls style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.warning(f"TTS failed: {e}")


def post_json(url: str, payload: dict, timeout: int = 25):
    """Safe POST wrapper."""
    try:
        resp = requests.post(url, json=payload, timeout=timeout)
        if not resp.ok:
            try:
                err = resp.json()
                msg = err.get("detail") or json.dumps(err)
            except:
                msg = resp.text
            raise RuntimeError(f"HTTP {resp.status_code}: {msg}")
        return resp.json()
    except Exception as e:
        raise RuntimeError(str(e))


def save_answer_to_backend(session_id: str, question_text: str, answer_text: str):
    """Save raw answer."""
    url = f"{BACKEND_HOST}/api/sessions/{session_id}/save-answer"
    payload = {"question": question_text, "answer": answer_text}
    try:
        post_json(url, payload)
        return True
    except Exception as e:
        st.error(f"Failed to save answer: {e}")
        return False


# -------------------------------------------
# MAIN INTERVIEW LOOP
# -------------------------------------------
if i < len(questions):
    q = questions[i]
    question_text = q.get("question") or str(q)

    st.subheader(f"Question {i + 1} / {len(questions)}")
    autoplay_text(question_text)
    st.info(question_text)
    st.warning("⏳ You have ~3–4 minutes to answer.")

    # VOICE RECORDER
    try:
        from streamlit_mic_recorder import speech_to_text
        transcribed = speech_to_text(
            language="en",
            start_prompt="🎤 Start Recording",
            stop_prompt="🛑 Stop Recording",
            key=f"mic_{i}",
        )
    except Exception:
        transcribed = None
        st.info("Microphone unavailable — use text input.")

    if transcribed:
        st.session_state.transcribed_answer = transcribed.strip()

    # TEXT INPUT
    final_answer = st.text_area(
        "Review / Edit your answer:",
        value=st.session_state.transcribed_answer or "",
        height=150,
        key=f"final_{i}",
    )

    # OPTIONAL CAMERA
    with st.sidebar:
        st.camera_input("📹 Optional Recording")

    # NEXT QUESTION BUTTON
    if st.button("Next Question ➡️"):
        if not final_answer.strip():
            st.warning("Please type or record your answer first.")
        else:
            save_answer_to_backend(
                st.session_state.session_id, question_text, final_answer
            )

            st.session_state.user_answers.append(
                {"question": question_text, "answer": final_answer}
            )
            st.session_state.transcribed_answer = ""
            st.session_state.current_question_index += 1
            st.rerun()

# -------------------------------------------
# INTERVIEW COMPLETE
# -------------------------------------------
else:
    st.success("🎉 Interview Complete! Great job.")
    st.balloons()

    st.subheader("Your Recorded Answers")
    for idx, a in enumerate(st.session_state.user_answers, start=1):
        st.write(f"**Q{idx}: {a['question']}**")
        st.write(a["answer"])
        st.markdown("---")

    # -------------------------------------------
    # LOCAL BACKUP
    # -------------------------------------------
    if st.button("💾 Save Local Backup"):
        folder = Path("user_responses")
        folder.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        sid = st.session_state.get("session_id", "unknown")
        fname = folder / f"user_responses_session_{sid}_{ts}.json"
        with open(fname, "w", encoding="utf-8") as f:
            json.dump(st.session_state.user_answers, f, indent=2)
        st.success(f"Saved: `{fname}`")

    # -------------------------------------------
    # EVALUATE ANSWERS (NEW FIXED)
    # -------------------------------------------
    if st.button("🎯 Evaluate My Answers"):
        session_id = st.session_state.session_id
        eval_url = f"{BACKEND_HOST}/api/sessions/{session_id}/evaluate-all"
        with st.spinner("Evaluating your answers..."):
            try:
                data = post_json(eval_url, {})
            except Exception as e:
                st.error(f"Evaluation failed: {e}")
                st.stop()

        per_q = data.get("evaluations") or []

        if not isinstance(per_q, list):
            st.error("Invalid evaluation format from backend.")
            st.write(data)
            st.stop()

        results = []
        for item in per_q:
            raw_score = item.get("final_score") or item.get("score") or 0.0

            try:
                score10 = round(float(raw_score) * 10, 1)
            except:
                score10 = raw_score

            results.append({
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "score": score10,
                "feedback": item.get("details", {}).get("feedback", "")
            })

        st.session_state.evaluation_results = results
        st.success("Evaluation complete! ✅")

        st.subheader("Evaluation Summary")
        results = []
        for idx, item in enumerate(per_q, start=1):
            raw_score = item.get("score") or item.get("final_score") or 0.0

            try:
                score10 = round(float(raw_score) * 10, 1)
            except:
                score10 = raw_score

            # Store full feedback for next page
            results.append({
                "question": item.get("question", ""),
                "answer": item.get("answer", ""),
                "score": score10,
                "feedback": item.get("details", {}).get("feedback", "")
            })

            # ===== SHOW ONLY SCORE HERE =====
            st.markdown(f"**Q{idx}. {item.get('question','')}**")
            st.write(f"**Your Answer:** {item.get('answer','')}")
            st.write(f"**Score:** {score10} / 20")
            st.markdown("---")

        # Save for feedback page
        st.session_state.evaluation_results = results

        st.success("Evaluation complete! Go to Final Feedback page ➜")
        st.page_link("pages/4_Feedback_Report.py", label="📊 View Final Analysis & Charts", icon="📈")

