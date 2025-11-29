import streamlit as st
import requests

# URL of your FastAPI backend
BACKEND_URL = "http://127.0.0.1:8080/api/get-domains"

st.set_page_config(page_title="AI Interview Coach", page_icon="🤖")

st.title("Automated Interview Coach 🤖")
st.header("Step 1: Resume Analysis")
st.write("Upload your resume, and our AI will identify your top 2 professional domains to tailor your interview prep.")

uploaded_file = st.file_uploader("Choose your resume...", type=["pdf", "docx"])

if uploaded_file is not None:
    st.info(f"Processed `{uploaded_file.name}`...")
    files = {"resume": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}

    try:
        with st.spinner('AI is analyzing your resume...'):
            response = requests.post(BACKEND_URL, files=files)

        if response.status_code == 200:
            st.success("Analysis Complete!")
            result = response.json()
            
            # --- FIX IS HERE ---
            # We must save all the necessary data to the session state for other pages to use.
            st.session_state.filename = result.get("filename")
            st.session_state.top_domains_data = result.get("top_domains", [])
            
            # Extract just the domain names for the selectbox
            domains = [d.get("domain_name") for d in st.session_state.top_domains_data if d.get("domain_name")]
            st.session_state.domains = domains

            st.subheader("🎯 Top Domains Identified")
            if st.session_state.top_domains_data:
                for domain_info in st.session_state.top_domains_data:
                     with st.container(border=True):
                        st.markdown(f"#### {domain_info.get('domain_name')}")
                        st.markdown("**Contributing Skills Found:**")
                        st.write(", ".join(domain_info.get('skills_found', [])))
                
                # Use st.page_link for navigation
                st.page_link("pages/1_Start_Interview.py", label="Proceed to Interview Setup", icon="➡️")
            else:
                st.warning("Could not determine top domains from your resume.")
        else:
            st.error(f"Error from server: {response.status_code} - {response.json().get('detail')}")

    except requests.exceptions.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        