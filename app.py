import streamlit as st
from fpdf import FPDF
from supabase import create_client
import hashlib
import os
import openai

# ---------------- CONFIG ----------------

st.set_page_config(page_title="HR Intelligence Tool", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

openai.api_key = os.getenv("OPENAI_API_KEY")

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""

# ---------------- UTIL ----------------

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- LOGIN ----------------

def login_page():

    st.title("HR Intelligence Platform")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pwd")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login", key="login_btn"):
            pwd = hash_password(password)

            data = supabase.table("users").select("*") \
                .eq("email", email) \
                .eq("password", pwd) \
                .execute()

            if data.data:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials")

    with col2:
        if st.button("Register", key="register_btn"):
            pwd = hash_password(password)

            supabase.table("users").insert({
                "email": email,
                "password": pwd
            }).execute()

            st.success("Account created. Login now.")

# ---------------- AI ANALYSIS ----------------

def analyze_resume(resume, jd):

    prompt = f"""
You are an enterprise HR analyst.

Resume:
{resume}

Job Description:
{jd}

Generate structured professional sections:

1. Insightful Analysis
2. Risk Flags
3. Hiring Signals
4. Interview Focus Areas
5. Culture and Soft Skill Hints
6. Gaps vs JD
7. Seniority Confidence
8. Hiring Recommendation Tone

Be specific and recruiter-grade.
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    return response.choices[0].message.content

# ---------------- PDF ----------------

def create_pdf(text):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=11)

    for line in text.split("\n"):
        pdf.multi_cell(0, 8, line)

    path = "analysis_report.pdf"
    pdf.output(path)

    return path

# ---------------- MAIN APP ----------------

def main_app():

    st.title("HR Intelligence Dashboard")

    nav = ["Resume Analyzer", "Download Report", "Logout"]

    page = st.sidebar.radio("Navigation", nav, key="nav_radio")

    # ---------------- ANALYZER ----------------

    if page == "Resume Analyzer":

        st.subheader("Candidate Evaluation")

        resume_text = st.text_area(
            "Paste Resume Text",
            height=250,
            key="resume_box"
        )

        jd_text = st.text_area(
            "Paste Job Description",
            height=250,
            key="jd_box"
        )

        if st.button("Run Analysis", key="analyze_btn"):

            if not resume_text or not jd_text:
                st.warning("Provide resume and JD")
            else:
                with st.spinner("Analyzing..."):
                    result = analyze_resume(resume_text, jd_text)
                    st.session_state.analysis_result = result

        if st.session_state.analysis_result:

            st.markdown("### HR Evaluation")
            st.write(st.session_state.analysis_result)

    # ---------------- PDF ----------------

    elif page == "Download Report":

        st.subheader("Export Analysis")

        if st.session_state.analysis_result:

            path = create_pdf(st.session_state.analysis_result)

            with open(path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name="HR_Analysis_Report.pdf",
                    key="pdf_btn"
                )

        else:
            st.info("Run analysis first")

    # ---------------- LOGOUT ----------------

    elif page == "Logout":
        st.session_state.logged_in = False
        st.rerun()

# ---------------- ROUTER ----------------

if st.session_state.logged_in:
    main_app()
else:
    login_page()
