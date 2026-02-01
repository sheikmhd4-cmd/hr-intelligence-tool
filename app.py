import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG & DB ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"

@st.cache_resource
def get_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = get_supabase()

# ---------------- PDF LOGIC (Outside Session to prevent crashes) ----------------
def create_pdf_data(res):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph("CANDIDATE ASSESSMENT REPORT", styles["Title"]),
        Spacer(1, 20),
        Paragraph(f"<b>Candidate Name:</b> {res['cand'] if res['cand'] else 'N/A'}", styles["Normal"]),
        Paragraph(f"<b>Suggested Role:</b> {res['role']}", styles["Normal"]),
        Paragraph(f"<b>Identified Skills:</b> {', '.join(res['skills'])}", styles["Normal"]),
        Spacer(1, 20),
        Paragraph("<b>Structured Interview Questions:</b>", styles["Heading2"]),
        Spacer(1, 10)
    ]
    for i, q in enumerate(res['questions'], 1):
        elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
        elements.append(Spacer(1, 5))
    doc.build(elements)
    return buf.getvalue()

# ---------------- APP START ----------------
st.set_page_config(page_title="HR Intel Portal", layout="wide")

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

# ---------------- AUTH UI ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        email = st.text_input("Corporate Email")
        password = st.text_input("Password", type="password")
        
        # நேரடி லாகின் - Form இல்லாமல்
        if st.button("Authenticate & Access", use_container_width=True):
            try:
                auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if auth.user:
                    st.session_state.auth_status = True
                    st.rerun()
            except:
                st.error("Authentication Failed. Check credentials.")

# ---------------- MAIN DASHBOARD ----------------
else:
    st.sidebar.success("Session Active")
    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.rerun()

    st.header("Candidate Evaluation Framework")
    
    col_l, col_r = st.columns([2, 1])
    with col_l:
        jd_text = st.text_area("Input Job Description", height=250)
    with col_r:
        c_name = st.text_input("Candidate Name", value="")
        level = st.select_slider("Target Level", ["Junior", "Mid", "Senior"])
        t_weight = st.slider("Technical Weight (%)", 0, 100, 70)

    if st.button("Process & Generate Summary", use_container_width=True) and jd_text:
        # Simple extraction
        db = ["python", "sql", "aws", "react", "marketing", "devops", "java", "api", "seo"]
        found = [s.capitalize() for s in db if s in jd_text.lower()]
        skills = found if found else ["General Professional"]
        
        # Session state-ல் சேமிப்பு
        st.session_state.results = {
            "cand": c_name,
            "skills": skills,
            "role": "Marketing Specialist" if "Marketing" in skills else "Software Engineer",
            "questions": [f"Explain your experience in {s}." for s in skills] + ["Describe a challenge you solved."],
            "tech": t_weight,
            "soft": 100 - t_weight
        }

    # முடிவுகள் இருந்தால் காண்பிக்கவும்
    if "results" in st.session_state and st.session_state.results:
        res = st.session_state.results
        st.divider()
        
        # ANALYSIS SUMMARY
        st.subheader("Analysis Summary")
        m1, m2 = st.columns([1.5, 1])
        with m1:
            st.write(f"**Candidate:** {res['cand'] if res['cand'] else 'N/A'}")
            st.write(f"**Skills:** {', '.join(res['skills'])}")
            st.info(f"Recommended Focus: {res['role']}")
        with m2:
            fig = go.Figure(data=[go.Pie(labels=['Tech', 'Soft'], values=[res['tech'], res['soft']], hole=.4)])
            fig.update_layout(height=200, margin=dict(l=0,r=0,b=0,t=0))
            st.plotly_chart(fig, use_container_width=True)

        # TARGETED QUESTIONS
        st.markdown("### Structured Interview Questions")
        for i, q in enumerate(res['questions'][:10], 1):
            st.info(f"{i}. {q}")

        # PDF DOWNLOAD (Zero-Error Method)
        pdf_data = create_pdf_data(res)
        st.download_button(
            label="📥 Download Detailed Report",
            data=pdf_data,
            file_name=f"Report_{res['cand']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )