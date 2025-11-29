# pages/2_Question_Generation.py
import streamlit as st
import requests
import json
from typing import Any

# NOTE: match your backend port
QUESTION_GEN_BASE = "http://127.0.0.1:8080"

# If you're using a third-party mic component make sure it's installed in your env.
# The import below is optional — if the component isn't available we'll degrade gracefully.
try:
    from streamlit_mic_recorder import speech_to_text  # type: ignore
    MIC_COMPONENT_AVAILABLE = True
except Exception:
    MIC_COMPONENT_AVAILABLE = False

st.set_page_config(page_title="Question Generation", page_icon="✨")

st.title("Question Generation ✨")

# Safety check: Ensure a session has been created before accessing this page.
if "session_id" not in st.session_state or not st.session_state.get("session_id"):
    st.warning("No active session found. Please start by creating a session.")
    # Use same style as other pages — if your app uses pages/ folder, give the pages path.
    st.page_link("pages/1_Start_Interview.py", label="Go to Session Setup", icon="⚙️")
    st.stop()

st.info(f"Working with Session ID: **{st.session_state.session_id}**")

# --- Permissions prompt (one-time) ---
st.header("Step 3: Grant Permissions (One-Time Setup)")
st.write("To ensure a smooth voice interview, please allow the browser to access your microphone and camera now.")
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### 🎙️ Microphone Check")
    if MIC_COMPONENT_AVAILABLE:
        # Render the mic recorder component; this will trigger a browser permission prompt.
        # We intentionally do not require the returned transcript here — just trigger permission.
        try:
            _ = speech_to_text(
                language="en",
                start_prompt="Click to allow microphone access (then click 'Stop').",
                stop_prompt="Microphone permission granted.",
                key="mic_permission_check",
            )
            st.caption("Microphone component rendered. If the browser asked for permission, you're good.")
        except Exception as e:
            st.warning("Mic component failed to render. Permission may not be requested automatically.")
            st.write(e)
    else:
        st.info("Microphone component not installed. Install `streamlit_mic_recorder` if you want browser mic permission flow.")

with col2:
    st.markdown("##### 📹 Camera Check")
    try:
        # camera_input triggers a camera permission prompt in browsers that support it.
        cam = st.camera_input("Click 'Allow' to grant camera permission (no need to take a photo).", key="camera_permission_check")
        if cam is not None:
            st.caption("Camera access granted.")
    except Exception as e:
        # Some Streamlit deploy targets or older browsers may not support camera_input.
        st.warning("Camera input not available in this environment.")
        st.write(e)

st.divider()

# --- Question generation UI ---
st.header("Step 4: Generate Your Questions")

def safe_post(url: str, json_payload: Any = None, timeout: int = 20) -> requests.Response:
    try:
        return requests.post(url, json=json_payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request failed: {e}")

# Only show the button if questions haven't been generated yet.
if "questions" not in st.session_state:
    if st.button("Generate Interview Questions", type="primary"):
        session_id = st.session_state.session_id
        question_gen_url = f"{QUESTION_GEN_BASE}/api/sessions/{session_id}/generate-questions"

        with st.spinner("Selecting questions from our bank..."):
            try:
                resp = safe_post(question_gen_url)
            except RuntimeError as e:
                st.error(str(e))
            else:
                if not resp.ok:
                    # try to give useful info from backend
                    try:
                        body = resp.json()
                        msg = body.get("detail") or json.dumps(body)
                    except Exception:
                        msg = resp.text or f"HTTP {resp.status_code}"
                    st.error(f"Failed to generate questions. Server message: {msg}")
                else:
                    try:
                        payload = resp.json()
                    except Exception:
                        st.error("Backend returned non-JSON response while generating questions.")
                        st.write(resp.text)
                    else:
                        # Expecting {"questions": [...]}
                        questions = payload.get("questions") if isinstance(payload, dict) else None
                        if not isinstance(questions, list):
                            st.error("Unexpected response structure from backend. Expected a 'questions' list.")
                            st.json(payload)
                        else:
                            st.session_state.questions = questions
                            st.session_state.current_question_index = 0
                            st.session_state.answers = []
                            # Rerun to show the interview launch UI
                            st.rerun()

# After generation: show guidelines and a clear path to start the interview
if "questions" in st.session_state:
    st.success("✅ Questions generated successfully!")
    st.warning(
        "⚠️ For a true interview experience: \n\n"
        "* Press **F11** for Full-Screen Mode.\n"
        "* Close other browser tabs and apps.\n"
        "* Be in a quiet environment."
    )
    # Link / navigation to the conduct-interview page.
    # Be consistent with your pages folder naming. Use a pages path to be safe.
    st.page_link("pages/3_Conduct_Interview.py", label="🎙️ Start Interview", icon="🎯")
