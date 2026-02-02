import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# ---------------- SESSION ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "results" not in st.session_state:
    st.session_state.results = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker",
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "Machine Learning",
    "data analysis": "Data Analysis", "devops": "DevOps",
    "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
    "java": "Java", "javascript": "JavaScript", "api": "API Development"
}

def extract_skills(text):
    text = text.lower()
    found = [v for k, v in SKILL_DB.items() if k in text]
    return list(set(found)) if found else ["General Technical"]

def generate_questions(skills, level):
    qs = []
    for s in skills:
        qs.extend([
            f"Explain fundamentals of {s}.",
            f"Describe a production project using {s}.",
            f"How do you debug failures in {s} systems?",
        ])
    while len(qs) < 10:
        qs.append("Explain a complex technical challenge you solved recently.")
    return qs[:12]

# --- 🛠 PDF GENERATOR FUNCTION (Saves from Error) ---
def create_pdf(res):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("INTERVIEW ASSESSMENT REPORT", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"<b>Candidate Name:</b> {res['cand'] if res['cand'] else 'N/A'}", styles["Normal"]),
        Paragraph(f"<b>Role:</b> {res['role']}", styles["Normal"]),
        Paragraph(f"<b>Detected Skills:</b> {', '.join(res['skills'])}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Targeted Interview Questions:</b>", styles["Heading2"]),
        Spacer(1, 10)
    ]
    for i, q in enumerate(res['questions'], 1):
        elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
        elements.append(Spacer(1, 5))
    doc.build(elements)
    return buf.getvalue()

# ---------------- AUTH UI ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        login_tab, _ = st.tabs(["Secure Login", "Registration"])
        with login_tab:
            email = st.text_input("Corporate Email")
            password = st.text_input("Password", type="password")
            role_choice = st.selectbox("Login as", ["Admin", "User"])
            if st.button("Authenticate & Enter", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.auth_status = True
                        st.session_state.user_role = role_choice
                        st.rerun()
                except:
                    st.error("Invalid credentials. Try again.")

# ---------------- MAIN APP ----------------
else:
    st.sidebar.markdown(f"### Role: {st.session_state.user_role.upper()}")
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment History"])

    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.session_state.results = None
        st.rerun()

    if page == "Framework Generator":
        st.header("Evaluation Framework")
        c1, c2 = st.columns([1.5, 1])
        with c1:
            jd = st.text_area("Input Job Description", height=260)
        with c2:
            cand = st.text_input("Candidate Name", value="") # காலியாக இருக்கும்
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weight (%)", 0, 100, 70)

        if st.button("Process Assessment", use_container_width=True) and jd:
            found_skills = extract_skills(jd)
            role = "Software Engineer"
            if "Machine Learning" in found_skills: role = "Data Scientist"
            elif "DevOps" in found_skills: role = "Cloud Engineer"
            
            st.session_state.results = {
                "cand": cand, "skills": found_skills, "role": role,
                "questions": generate_questions(found_skills, level),
                "tech": tech_w, "soft": 100 - tech_w
            }

        if st.session_state.results:
            res = st.session_state.results
            st.divider()
            r1, r2 = st.columns(2)
            with r1:
                st.subheader("Analysis Summary")
                st.write(f"**Candidate:** {res['cand'] if res['cand'] else 'N/A'}")
                st.write(f"**Skills:** {', '.join(res['skills'])}")
                st.info(f"Recommended Role: {res['role']}")
            with r2:
                fig = go.Figure(data=[go.Pie(labels=["Tech", "Soft"], values=[res['tech'], res['soft']], hole=0.4)])
                fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig, use_container_width=True)

            for i, q in enumerate(res['questions'], 1):
                st.info(f"{i}. {q}")

            # பட்டனை அழுத்தும் போது மட்டும் PDF உருவாக்கப்படும் - இதுதான் எரரை தடுக்கும்
            st.download_button(
                label="📥 Download Professional Report",
                data=create_pdf(res),
                file_name=f"Assessment_{res['cand']}.pdf" if res['cand'] else "Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    elif page == "Assessment History":
        st.header("Enterprise Audit Logs")
        st.info("Database records will appear here.")