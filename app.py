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

# ---------------- AUTH CHECK ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    # Simplified Login for quick testing
    st.title("HR Intelligence Portal")
    email = st.text_input("Corporate Email")
    password = st.text_input("Password", type="password")
    if st.button("Login", use_container_width=True):
        try:
            supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.auth_status = True
            st.rerun()
        except: st.error("Login Failed")
else:
    # ---------------- MAIN APP ----------------
    st.sidebar.title("HR Intel")
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment Logs"])

    if page == "Framework Generator":
        st.header("Assessment Framework Generator")
        
        col_jd, col_ctrl = st.columns([1.5, 1])
        
        with col_jd:
            jd = st.text_area("Paste Job Description Here", height=250)
        
        with col_ctrl:
            cand_name = st.text_input("Candidate Name")
            difficulty = st.select_slider("Seniority Level", options=["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Focus (%)", 0, 100, 70)
            soft_w = 100 - tech_w

        if st.button("Generate Evaluation Framework", use_container_width=True) and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            # --- PIE CHART & SUMMARY SECTION ---
            st.divider()
            res_col1, res_col2 = st.columns([1, 1])
            
            with res_col1:
                st.subheader("Evaluation Summary")
                st.write(f"**Candidate:** {cand_name}")
                st.write(f"**Target Level:** {difficulty}")
                st.write(f"**Skills Found:** {', '.join(skills) if skills else 'N/A'}")
                
            with res_col2:
                # Plotly Pie Chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Technical', 'Soft Skills'], 
                    values=[tech_w, soft_w],
                    hole=.4,
                    marker_colors=['#1E3A8A', '#94A3B8']
                )])
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=250, showlegend=True)
                st.plotly_chart(fig, use_container_width=True)

            # --- QUESTIONS SECTION ---
            st.subheader("Targeted Interview Questions")
            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

            # --- PDF GENERATION (Professional Table Style) ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            title_s = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#1E3A8A"))
            
            elements = [
                Paragraph("CANDIDATE ASSESSMENT REPORT", title_s),
                Spacer(1, 20),
                Table([
                    ["Candidate:", cand_name],
                    ["Seniority:", difficulty],
                    ["Tech Weight:", f"{tech_w}%"],
                    ["Soft Skills:", f"{soft_w}%"]
                ], style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke)])),
                Spacer(1, 20),
                Paragraph("<b>Interview Questions:</b>", styles['Heading3'])
            ]
            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"{i}. {q}", styles['Normal']))
                elements.append(Spacer(1, 5))
            
            doc.build(elements)
            
            st.download_button(
                label="📥 Download Detailed Report",
                data=buffer.getvalue(),
                file_name=f"Report_{cand_name}.pdf",
                mime="application/pdf"
            )

    elif page == "Assessment Logs":
        st.header("Database Records")
        res = supabase.table("candidate_results").select("*").execute()
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)