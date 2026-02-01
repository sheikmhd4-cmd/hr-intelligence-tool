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

# ---------------- SESSION MANAGEMENT ----------------
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
    "marketing": "Marketing Strategy", "seo": "SEO/SEM", "api": "API Development"
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

# --- 🛠 SECURE PDF GENERATOR ---
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

# ---------------- AUTHENTICATION UI ----------------
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
                    # Single-click logic
                    res_auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res_auth.user:
                        st.session_state.auth_status = True
                        st.session_state.user_role = role_choice
                        st.rerun()
                except:
                    st.error("Authentication failed. Please check credentials.")
else:
    # ---------------- MAIN APP ----------------
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
            jd_input = st.text_area("Input Job Description", height=260)
        with c2:
            cand_name = st.text_input("Candidate Name", value="") # Empty by default
            level_sel = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weight (%)", 0, 100, 70)

        if st.button("Process Assessment", use_container_width=True) and jd_input:
            skills_found = extract_skills(jd_input)
            role_type = "Software Engineer"
            if any(x in ["Marketing Strategy", "SEO/SEM"] for x in skills_found):
                role_type = "Marketing Manager"
            
            st.session_state.results = {
                "cand": cand_name, 
                "skills": skills_found, 
                "role": role_type,
                "questions": generate_questions(skills_found, level_sel),
                "tech": tech_w, 
                "soft": 100 - tech_w
            }

        if st.session_state.results:
            res = st.session_state.results
            st.divider()
            
            r1, r2 = st.columns(2)
            with r1:
                st.subheader("Analysis Summary")
                st.write(f"**Candidate:** {res['cand'] if res['cand'] else 'N/A'}")
                st.write(f"**Detected Skills:** {', '.join(res['skills'])}")
                st.info(f"Recommended Role: {res['role']}")
            with r2:
                fig = go.Figure(data=[go.Pie(labels=["Technical", "Soft"], values=[res['tech'], res['soft']], hole=0.45)])
                fig.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig, use_container_width=True)

            # --- HEADING ADDED BACK ---
            st.markdown("### Targeted Interview Questions")
            for i, q in enumerate(res['questions'], 1):
                st.info(f"{i}. {q}")

            # --- SECURE DOWNLOAD BUTTON ---
            st.download_button(
                label="📥 Download Professional Assessment Report",
                data=create_pdf(res), # Creates PDF only on click
                file_name=f"Assessment_{res['cand']}.pdf" if res['cand'] else "Assessment_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    elif page == "Assessment History":
        st.header("Assessment History")
        st.info("Database connection active. Records will load here.")