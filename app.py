import streamlit as st
from fpdf import FPDF
from supabase import create_client
import hashlib
import os
import io
from openai import OpenAI

# ---------------- CONFIG & SECRETS ----------------

st.set_page_config(page_title="HR Intelligence Tool", layout="wide")

# Safe ah keys edukarom
try:
    S_URL = st.secrets["SUPABASE_URL"]
    S_KEY = st.secrets["SUPABASE_KEY"]
    O_KEY = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("❌ Secrets Missing! Streamlit Cloud Settings -> Secrets la keys update pannunga.")
    st.stop()

client = OpenAI(api_key=O_KEY)
supabase = create_client(S_URL, S_KEY)

# ---------------- SESSION INIT ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ---------------- UTILS ----------------

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def create_pdf(text):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Encoding fix for special characters
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    
    for block in clean_text.split("\n"):
        pdf.multi_cell(0, 8, block)
    
    return pdf.output(dest='S').encode('latin-1')

# ---------------- AI ENGINE ----------------

def analyze_resume(resume_text, jd_text):
    prompt = f"""
    You are a senior corporate HR partner. Evaluate the candidate in depth.
    Resume: {resume_text}
    JD: {jd_text}
    
    Sections:
    ### Insightful Analysis
    ### Identified Competencies
    ### Structured Interview Questions
    ### Hiring Recommendation
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Error: {str(e)}"

# ---------------- UI: LOGIN & REGISTER ----------------

def auth_page():
    st.title("HR Intelligence Platform")
    
    # Old UI: Tabs for Login/Register
    tab1, tab2 = st.tabs(["Secure Login", "New Registration"])
    
    with tab1:
        email = st.text_input("Corporate Email", key="login_email")
        pwd = st.text_input("Password", type="password", key="login_pwd")
        
        if st.button("Authenticate & Enter", use_container_width=True):
            hashed = hash_password(pwd)
            try:
                res = supabase.table("users").select("*").eq("email", email).eq("password", hashed).execute()
                if res.data:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.rerun()
                else:
                    st.error("Invalid Email or Password")
            except Exception as e:
                st.error("Database connection issue. 'users' table irukanu check pannunga.")

    with tab2:
        new_email = st.text_input("New Email", key="reg_email")
        new_pwd = st.text_input("New Password", type="password", key="reg_pwd")
        
        if st.button("Create Account", use_container_width=True):
            if not new_email or not new_pwd:
                st.warning("Please provide both email and password.")
            else:
                hashed_pwd = hash_password(new_pwd)
                try:
                    supabase.table("users").insert({
                        "email": new_email,
                        "password": hashed_pwd
                    }).execute()
                    st.success("✅ Account created successfully! Go to Login tab.")
                except Exception as e:
                    st.error("Registration failed. Table 'users' created-ah? (OR) Email already exists.")
                    st.info("Check: Supabase -> Table Editor -> users (columns: email, password)")

# ---------------- UI: MAIN DASHBOARD ----------------

def main_app():
    st.sidebar.title(f"User: {st.session_state.user_email.split('@')[0]}")
    page = st.sidebar.radio("Navigation", ["Resume Analyzer", "Logout"])

    if page == "Logout":
        st.session_state.logged_in = False
        st.session_state.analysis_result = ""
        st.rerun()

    if page == "Resume Analyzer":
        st.header("Candidate Evaluation Framework")
        
        c1, c2 = st.columns(2)
        with c1:
            res_txt = st.text_area("Paste Resume", height=250, placeholder="Full text of candidate resume...")
        with c2:
            jd_txt = st.text_area("Paste JD", height=250, placeholder="Full job description...")

        if st.button("Run Intelligence Analysis", use_container_width=True):
            if res_txt and jd_txt:
                with st.spinner("Analyzing candidate profile..."):
                    result = analyze_resume(res_txt, jd_txt)
                    st.session_state.analysis_result = result
            else:
                st.warning("Paste both Resume and JD to proceed.")

        if st.session_state.analysis_result:
            st.divider()
            st.markdown(st.session_state.analysis_result)
            
            pdf_bytes = create_pdf(st.session_state.analysis_result)
            st.download_button(
                label="📥 Download Professional Assessment Report",
                data=pdf_bytes,
                file_name=f"Assessment_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

# ---------------- ROUTER ----------------

if st.session_state.logged_in:
    main_app()
else:
    auth_page()