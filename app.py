import streamlit as st
import os
from openai import OpenAI
from supabase import create_client

# ---------------- CONFIG ----------------

# 1. முதலில் கீகளைப் பெற முயற்சிப்போம்
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 2. முக்கியமான செக்: கீ இல்லையென்றால் இங்கேயே நிறுத்திவிடுவோம்
if not OPENAI_KEY:
    st.error("❌ OpenAI API Key கிடைக்கவில்லை! Streamlit Secrets-ல் 'OPENAI_API_KEY' சரியாக உள்ளதா எனப் பார்க்கவும்.")
    st.stop() # இது எரர் கிராஷ் ஆவதைத் தடுக்கும்

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Supabase Credentials கிடைக்கவில்லை!")
    st.stop()

# 3. இப்போது Client-களை உருவாக்கலாம் (இங்கேதான் எரர் வந்தது, இப்போது வராது)
client = OpenAI(api_key=OPENAI_KEY)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- REST OF THE CODE ----------------
# உங்கள் மீதமுள்ள கோட் இங்கே தொடரும்...

# ---------------- SESSION INIT ----------------

defaults = {
    "logged_in": False,
    "analysis_result": "",
    "user_email": "",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------- UTIL ----------------

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

# ---------------- LOGIN PAGE ----------------

def login_page():

    st.title("HR Intelligence Platform")

    email = st.text_input("Email", key="login_email_input")
    password = st.text_input(
        "Password",
        type="password",
        key="login_password_input"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login", key="login_btn_main"):

            hashed = hash_password(password)

            res = (
                supabase
                .table("users")
                .select("*")
                .eq("email", email)
                .eq("password", hashed)
                .execute()
            )

            if res.data:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Invalid email or password")

    with col2:
        if st.button("Register", key="register_btn_main"):

            if not email or not password:
                st.warning("Provide email and password")
                return

            hashed = hash_password(password)

            supabase.table("users").insert({
                "email": email,
                "password": hashed
            }).execute()

            st.success("Account created. Please login.")

# ---------------- AI ENGINE ----------------

def analyze_resume(resume_text, jd_text):

    prompt = f"""
You are a senior corporate HR partner and talent strategist at a Fortune 500 company.

Evaluate the candidate in a deep, narrative, recruiter-grade manner.

Resume:
{resume_text}

Job Description:
{jd_text}

Produce LONG paragraph-form professional sections:

### Insightful Analysis
Explain profile trajectory, strengths, domain depth, and career maturity.

### Risk Flags
Discuss stability risks, skill gaps, unclear transitions, technical depth doubts.

### Hiring Signals
Highlight concrete indicators of strong hire potential.

### Interview Focus Areas
Provide probing topics and technical/behavioral angles.

### Culture and Soft-Skill Hints
Infer leadership style, communication, ownership, adaptability.

### Gaps vs JD
Compare point-by-point with JD expectations.

### Seniority Confidence
Assess level fit and growth readiness.

### Hiring Recommendation Tone
State whether to proceed aggressively, cautiously, or reject, with justification.

Write dense, professional paragraphs, not bullet points.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return response.choices[0].message.content

# ---------------- PDF BUILDER ----------------

def create_pdf(text):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for block in text.split("\n"):
        pdf.multi_cell(0, 8, block)

    path = "HR_Report.pdf"
    pdf.output(path)

    return path

# ---------------- MAIN APP ----------------

def main_app():

    st.title("HR Intelligence Dashboard")

    nav = [
        "Resume Analyzer",
        "Download Report",
        "Logout"
    ]

    page = st.sidebar.radio(
        "Navigation",
        nav,
        key="nav_radio_main"
    )

    # ---------- ANALYZER ----------

    if page == "Resume Analyzer":

        st.subheader("Candidate Evaluation")

        resume_text = st.text_area(
            "Paste Resume Text",
            height=260,
            key="resume_input_box"
        )

        jd_text = st.text_area(
            "Paste Job Description",
            height=260,
            key="jd_input_box"
        )

        if st.button("Run Analysis", key="run_analysis_btn"):

            if not resume_text or not jd_text:
                st.warning("Resume and Job Description required")
            else:
                with st.spinner("Generating evaluation..."):
                    result = analyze_resume(
                        resume_text,
                        jd_text
                    )

                    st.session_state.analysis_result = result

        if st.session_state.analysis_result:

            st.markdown("## HR Evaluation Report")
            st.write(st.session_state.analysis_result)

    # ---------- DOWNLOAD ----------

    elif page == "Download Report":

        st.subheader("Export Report")

        if st.session_state.analysis_result:

            pdf_path = create_pdf(
                st.session_state.analysis_result
            )

            with open(pdf_path, "rb") as f:
                st.download_button(
                    "Download PDF",
                    f,
                    file_name="HR_Intelligence_Report.pdf",
                    key="download_pdf_btn"
                )
        else:
            st.info("Run an analysis first.")

    # ---------- LOGOUT ----------

    elif page == "Logout":

        st.session_state.logged_in = False
        st.session_state.analysis_result = ""
        st.session_state.user_email = ""
        st.rerun()

# ---------------- ROUTER ----------------

if st.session_state.logged_in:
    main_app()
else:
    login_page()
