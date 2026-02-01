import streamlit as st
import pandas as pd
from supabase import create_client
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
        if level == "Junior": qs.append(f"Foundational concepts of {s} and practical usage.")
        elif level == "Mid": qs.append(f"Implementation strategies and troubleshooting {s}.")
        else: qs.append(f"Architectural decision-making and optimization using {s}.")
    return qs

# ---------------- AUTH & MAIN APP ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    # (Login UI remains same as previous clean version)
    st.title("HR Intelligence Portal")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        try:
            supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.auth_status = True
            st.rerun()
        except: st.error("Login Failed")
else:
    st.sidebar.title("HR Intel")
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment Logs"])

    if page == "Framework Generator":
        st.header("Assessment Framework Generator")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            jd = st.text_area("Paste Job Description Here", height=250)
        with col2:
            cand_name = st.text_input("Candidate Name")
            difficulty = st.select_slider("Level", options=["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weightage (%)", 0, 100, 70)
            soft_w = 100 - tech_w

        if st.button("Generate Full Report") and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            # Database Save
            try:
                supabase.table("candidate_results").insert({
                    "candidate_name": cand_name, "jd_role": f"{difficulty} Specialist",
                    "total_score": float(tech_w), "created_by": "Admin"
                }).execute()
            except: pass

            # --- PDF GENERATION (Multi-Section Report) ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_s = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#1E3A8A"), spaceAfter=10)
            head_s = ParagraphStyle('H', parent=styles['Heading3'], textColor=colors.HexColor("#2563EB"), spaceBefore=10)
            body_s = styles['Normal']

            elements = []
            
            # 1. Header Area
            elements.append(Paragraph("CANDIDATE ASSESSMENT FRAMEWORK", title_s))
            elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=20))
            
            # 2. Summary Table (Like your 2nd pic)
            data = [
                ["Candidate Name:", cand_name],
                ["Seniority Level:", difficulty],
                ["Technical Weightage:", f"{tech_w}%"],
                ["Soft Skills Weightage:", f"{soft_w}%"]
            ]
            t = Table(data, colWidths=[150, 300])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('PADDING', (0,0), (-1,-1), 8)
            ]))
            elements.append(t)
            elements.append(Spacer(1, 20))

            # 3. Identified Skills Section
            elements.append(Paragraph("IDENTIFIED COMPETENCIES", head_s))
            elements.append(Paragraph(", ".join(skills) if skills else "General Evaluation", body_s))
            elements.append(Spacer(1, 15))

            # 4. Structured Questions Section
            elements.append(Paragraph("STRUCTURED INTERVIEW QUESTIONS", head_s))
            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"<b>{i}.</b> {q}", body_s))
                elements.append(Spacer(1, 8))

            doc.build(elements)
            
            st.success("Report Generated Successfully!")
            st.download_button(
                label="📥 Download Detailed Assessment PDF",
                data=buffer.getvalue(),
                file_name=f"Detailed_Report_{cand_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )