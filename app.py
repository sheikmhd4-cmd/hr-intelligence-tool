import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# Session State Init
if "auth_status" not in st.session_state: st.session_state.auth_status = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "current_report" not in st.session_state: st.session_state.current_report = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {"python": "Python", "sql": "SQL", "docker": "Docker", "aws": "AWS", "react": "React", "devops": "DevOps"}

def extract_skills(text):
    return list(set([v for k, v in SKILL_DB.items() if k in text.lower()]))

def generate_questions(skills, level):
    return [f"Explain {s} implementation for {level} role." for s in skills]

# ---------------- AUTH ----------------
if not st.session_state.auth_status:
    with st.form("login"):
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "User"])
        if st.form_submit_button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": pw})
                if res.user:
                    st.session_state.auth_status, st.session_state.user_role = True, role
                    st.rerun()
            except: st.error("Failed")

# ---------------- APP ----------------
else:
    st.sidebar.write(f"Logged in as: {st.session_state.user_role}")
    page = st.sidebar.radio("Menu", ["Generator", "History"] if st.session_state.user_role == "Admin" else ["Generator"])

    if page == "Generator":
        st.header("Assessment Generator")
        jd = st.text_area("JD Text")
        name = st.text_input("Candidate Name")
        tech = st.slider("Tech Weight", 0, 100, 70)
        
        if st.button("Generate Result"):
            skills = extract_skills(jd)
            qs = generate_questions(skills, "Senior")
            # முக்கியமானது: டேட்டாவை இங்க சேமிக்கிறோம்
            st.session_state.current_report = {"name": name, "skills": skills, "qs": qs, "tech": tech}
            
            # DB insert
            supabase.table("candidate_results").insert({"candidate_name": name, "total_score": float(tech)}).execute()

        # ரிப்போர்ட் இருந்தால் மட்டும் UI மற்றும் PDF-ஐக் காட்டு
        if st.session_state.current_report:
            rep = st.session_state.current_report
            st.divider()
            st.subheader(f"Summary for {rep['name']}")
            
            # UI display
            c1, c2 = st.columns(2)
            c1.write(f"Skills: {', '.join(rep['skills'])}")
            fig = go.Figure(data=[go.Pie(labels=['Tech', 'Soft'], values=[rep['tech'], 100-rep['tech']])])
            c2.plotly_chart(fig)

            # PDF Build Logic (Directly inside button to ensure data is fresh)
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph("CANDIDATE REPORT", styles['Title']),
                Spacer(1, 12),
                Paragraph(f"<b>Name:</b> {rep['name']}", styles['Normal']),
                Paragraph(f"<b>Skills:</b> {', '.join(rep['skills'])}", styles['Normal']),
                Spacer(1, 12),
                Paragraph("<b>Interview Questions:</b>", styles['Heading3'])
            ]
            for q in rep['qs']:
                elements.append(Paragraph(f"• {q}", styles['Normal']))
            
            doc.build(elements)
            
            st.download_button("📥 Download PDF", buffer.getvalue(), "Report.pdf", "application/pdf")

    elif page == "History":
        res = supabase.table("candidate_results").select("*").execute()
        st.dataframe(pd.DataFrame(res.data))