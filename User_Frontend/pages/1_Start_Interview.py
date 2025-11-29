# pages/1_Start_Interview.py
import streamlit as st
import requests
import json

# Match your FastAPI backend port (8080 if you're running uvicorn main:app --reload --port 8080)
SESSION_API_URL = "http://127.0.0.1:8080/api/sessions"

st.set_page_config(page_title="Interview Setup", page_icon="⚙️")

st.title("Interview Setup ⚙️")

# Defensive session_state initialization
st.session_state.setdefault("domains", [])
st.session_state.setdefault("top_domains_data", [])
st.session_state.setdefault("filename", None)

# --- Check if previous step was completed ---
if not st.session_state.domains:
    st.warning("⚠️ Please upload your resume on the main page first to identify your domains.")
    st.page_link("app.py", label="⬅️ Back to Home")
    st.stop()

st.header("Step 2: Configure Your Interview")
st.write("Confirm your domain and select a difficulty level to begin your interview session.")

selected_domain = st.selectbox(
    "Choose your primary domain:",
    st.session_state.domains,
    index=0 if st.session_state.domains else None
)

difficulty = st.radio(
    "Select difficulty level:",
    ["Easy", "Medium", "Hard"],
    horizontal=True,
    index=1
)

st.divider()
st.write("Click below to create your interview session on the backend and get a unique session ID.")

def create_session(payload: dict) -> dict:
    """Create an interview session via backend."""
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(SESSION_API_URL, json=payload, headers=headers, timeout=20)
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Connection failed: {e}")

    if not resp.ok:
        try:
            body = resp.json()
            msg = body.get("detail") or json.dumps(body)
        except Exception:
            msg = resp.text or f"HTTP {resp.status_code}"
        raise RuntimeError(f"Backend error: {msg}")

    try:
        return resp.json()
    except Exception:
        raise RuntimeError("Backend returned invalid JSON response.")

if st.button("🚀 Start Interview Session", type="primary"):
    session_payload = {
        "selected_domain": selected_domain,
        "difficulty_level": difficulty,
        "resume_analysis_result": {
            "filename": st.session_state.filename,
            "top_domains": st.session_state.top_domains_data
        }
    }

    with st.spinner("Creating interview session..."):
        try:
            session_info = create_session(session_payload)
            session_id = (
                session_info.get("id")
                or session_info.get("session_id")
                or session_info.get("uuid")
            )
            if not session_id:
                st.error("Backend responded but no session ID was found.")
                st.json(session_info)
            else:
                st.session_state.session_id = session_id
                st.success(f"✅ Interview session created successfully!")

        except RuntimeError as e:
            st.error(f"❌ Failed to create session: {e}")
        except Exception as e:
            st.exception(e)

# --- Proceed to Next Step ---
if st.session_state.get("session_id"):
    st.divider()
    st.success(f"Session ready — ID: **{st.session_state.session_id}**")
    st.page_link("pages/2_Question_Generation.py", label="➡️ Next: Generate Questions")
