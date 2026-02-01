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
# Result-ஐ சேமிக்க Session State (To fix "Site can't be reached" error)
if "results" not in st.session_state:
    st.session_state.results = None

# ---------------- CORE ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker",
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "Machine Learning",
    "data analysis": "Data Analysis", "devops": "DevOps",
    "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

def extract_skills(text):
    found = [v for k, v in SKILL_DB.items() if k in text.lower()]
    return list(set(found))

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

def generate_summary(skills, level, tech):
    role = "Software Engineer"
    if "Machine Learning" in skills: role = "Data Scientist / ML Engineer"
    elif "DevOps" in skills: role = "Cloud / DevOps Engineer"
    elif "React" in skills: role = "Frontend Engineer"
    
    focus = "Technical Heavy" if tech >= 65 else "Balanced"
    insight = f"JD focuses on {', '.join(skills)}. Targeted for {level} role."
    return role, focus, insight

# ---------------- AUTH ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        login_tab, _ = st.tabs(["Secure Login", "Registration"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Corporate Email")
                password = st.text_input("Password", type="password")
                role_choice = st.selectbox("Login as", ["Admin", "User"])
                if st.form_submit_button("Authenticate", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res.user:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.rerun()
                    except: st.error("Authentication failed.")
else:
    st.sidebar.markdown(f"### Role: {st.session_state.user_role.upper()}")
    nav = ["Framework Generator"]
    if st.session_state.user_role == "Admin": nav.append("Assessment History")
    page = st.sidebar.radio("Navigation", nav)

    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Framework Generator":
        st.header("Evaluation Framework")
        c1, c2 = st.columns([1.5, 1])
        with c1: jd = st.text_area("Input Job Description", height=260)
        with c2:
            cand = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech = st.slider("Technical Weight (%)", 0, 100, 70)

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            role, focus, insight = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)
            
            # Save to session state to prevent PDF data loss on rerun
            st.session_state.results = {
                "cand": cand, "skills": skills, "role": role, 
                "focus": focus, "insight": insight, "questions": questions,
                "tech": tech, "soft": 100 - tech
            }

        if st.session_state.results:
            res = st.session_state.results
            st.divider()
            r1, r2 = st.columns([1, 1])
            with r1:
                st.subheader("Live Result Summary")
                st.write(f"**Candidate:** {res['cand'] if res['cand'] else 'N/A'}")
                st.write(f"**Detected Skills:** {', '.join(res['skills'])}")
                st.write(f"**Suggested Role:** {res['role']}")
                st.info(res['insight'])
            with r2:
                fig = go.Figure(data=[go.Pie(labels=["Technical", "Soft Skills"], values=[res['tech'], res['soft']], hole=0.45)])
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

            for i, q in enumerate(res['questions'], 1): st.info(f"{i}. {q}")

            # PDF Generation logic (Safe from "Site can't be reached")
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph("INTERVIEW ASSESSMENT REPORT", styles["Title"]),
                Spacer(1, 12),
                Paragraph(f"<b>Candidate:</b> {res['cand']}", styles["Normal"]),
                Paragraph(f"<b>Role:</b> {res['role']}", styles["Normal"]),
                Spacer(1, 12)
            ]
            for i, q in enumerate(res['questions'], 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
            
            doc.build(elements)
            st.download_button(
                "📥 Download Report",
                data=pdf_buffer.getvalue(),
                file_name=f"Assessment_{res['cand']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    elif page == "Assessment History":
        st.header("Enterprise Audit Logs")
        hist = supabase.table("candidate_results").select("*").execute()
        st.dataframe(pd.DataFrame(hist.data), use_container_width=True)