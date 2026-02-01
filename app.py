import streamlit as st
import pandas as pd
from supabase import create_client
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "ML", "data analysis": "Data",
    "devops": "DevOps", "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

def extract_skills(text):
    found = []
    t = text.lower()
    for k, v in SKILL_DB.items():
        if k in t: found.append(v)
    return list(set(found))

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior": qs.append(f"Foundational concepts of {s} and practical implementation.")
        elif level == "Mid": qs.append(f"Advanced implementation strategies and system troubleshooting for {s}.")
        else: qs.append(f"High-level architecture, scalability, and optimization using {s}.")
    return qs

# ---------------- AUTH UI ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        tabs = st.tabs(["Secure Access", "System Registration"])
        with tabs[0]:
            email = st.text_input("Corporate Email")
            password = st.text_input("Security Token", type="password")
            if st.button("Authenticate Session", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.auth_status = True
                    st.session_state.user_role = "Admin"
                    st.rerun()
                except: st.error("Credential verification failed.")
        with tabs[1]:
            new_email = st.text_input("Registration Email")
            new_pass = st.text_input("Set Security Token", type="password")
            if st.button("Initialize Account", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pass})
                    st.info("Registration logged. Please proceed to login.")
                except Exception as e: st.error(f"System Error: {str(e)}")

# ---------------- MAIN APP ----------------
else:
    st.sidebar.markdown(f"**Session:** {st.session_state.user_role}")
    st.sidebar.divider()
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment Logs"])
    
    if st.sidebar.button("Logout Session", use_container_width=True):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Framework Generator":
        st.header("Candidate Evaluation Framework")
        col_main, col_side = st.columns([2, 1])
        
        with col_main:
            uploaded_file = st.file_uploader("Job Specification (TXT)", type=["txt"])
            jd = uploaded_file.read().decode("utf-8") if uploaded_file else st.text_area("Input Job Description Text", height=300)

        with col_side:
            st.subheader("Assessment Controls")
            difficulty = st.select_slider("Target Seniority", options=["Junior", "Mid", "Senior"])
            cand_name = st.text_input("Full Candidate Name", placeholder="Enter name...")
            tech_w = st.slider("Technical Weightage (%)", 0, 100, 70)
            soft_w = 100 - tech_w

        if st.button("Process & Generate Framework", use_container_width=True) and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            st.divider()
            st.subheader(f"Evaluation Summary: {cand_name}")
            m1, m2, m3 = st.columns(3)
            m1.metric("Competencies Found", len(skills))
            m2.metric("Difficulty Level", difficulty)
            m3.metric("Technical Focus", f"{tech_w}%")

            # Database Sync
            try:
                history_entry = {
                    "candidate_name": cand_name if cand_name else "Unknown",
                    "jd_role": f"{difficulty} Specialist",
                    "total_score": float(tech_w),
                    "created_by": "Admin"
                }
                supabase.table("candidate_results").insert(history_entry).execute()
                st.success("Record archived successfully.")
            except: pass

            # --- PDF GENERATION (Fixed AttributeError) ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # FIXED: Used colors.HexColor instead of colors.hexColor
            title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor("#1E3A8A"), fontSize=20, spaceAfter=20)
            heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading3'], textColor=colors.HexColor("#334155"), spaceBefore=12, spaceAfter=8)

            elements = []
            elements.append(Paragraph("INTERVIEW ASSESSMENT FRAMEWORK", title_style))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey, spaceAfter=15))
            elements.append(Paragraph(f"<b>Candidate Name:</b> {cand_name}", styles['Normal']))
            elements.append(Paragraph(f"<b>Seniority Level:</b> {difficulty}", styles['Normal']))
            elements.append(Paragraph(f"<b>Technical Weightage:</b> {tech_w}% | <b>Soft Skills:</b> {soft_w}%", styles['Normal']))
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("EXTRACTED COMPETENCIES", heading_style))
            elements.append(Paragraph(", ".join(skills) if skills else "N/A", styles['Normal']))
            elements.append(Paragraph("STRUCTURED INTERVIEW QUESTIONS", heading_style))
            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"{i}. {q}", styles['Normal']))
                elements.append(Spacer(1, 6))

            doc.build(elements)
            st.download_button(label="📥 Download Professional Assessment Report", data=buffer.getvalue(), file_name=f"Assessment_{cand_name}.pdf", mime="application/pdf", use_container_width=True)

    elif page == "Assessment Logs":
        st.header("Enterprise Evaluation Logs")
        res = supabase.table("candidate_results").select("*").execute()
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)