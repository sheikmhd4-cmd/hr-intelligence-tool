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

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "ML", "data analysis": "Data",
    "devops": "DevOps", "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

def extract_skills(text):
    found = [v for k, v in SKILL_DB.items() if k in text.lower()]
    return list(set(found))

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior": qs.append(f"Foundational concepts of {s} and practical usage.")
        elif level == "Mid": qs.append(f"Implementation strategies and troubleshooting {s}.")
        else: qs.append(f"Architectural decision-making and optimization using {s}.")
    return qs

# ---------------- AUTH UI ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        tabs = st.tabs(["Secure Login", "Registration"])
        with tabs[0]:
            email = st.text_input("Corporate Email", key="l_email")
            password = st.text_input("Password", type="password", key="l_pw")
            role_choice = st.selectbox("Login as", ["Admin", "User"]) 
            if st.button("Authenticate", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.auth_status = True
                        st.session_state.user_role = role_choice
                        st.rerun()
                except: st.error("Authentication failed.")

# ---------------- MAIN APP ----------------
else:
    st.sidebar.markdown(f"### Role: **{st.session_state.user_role.upper()}**")
    
    # Navigation logic based on Role
    nav_options = ["Framework Generator"]
    if st.session_state.user_role == "Admin":
        nav_options.append("Assessment History (Admin Only)")
    
    page = st.sidebar.radio("Navigation", nav_options)
    
    if st.sidebar.button("Logout Session", use_container_width=True):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Framework Generator":
        st.header("Evaluation Framework")
        col_jd, col_p = st.columns([1.5, 1])
        with col_jd:
            jd = st.text_area("Input Job Description", height=250)
        with col_p:
            cand_name = st.text_input("Candidate Name")
            difficulty = st.select_slider("Level", options=["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weight (%)", 0, 100, 70)
            soft_w = 100 - tech_w

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            # Display LIVE Result for both Admin and User
            st.divider()
            r1, r2 = st.columns([1, 1])
            with r1:
                st.subheader("Live Result Summary")
                st.write(f"**Candidate:** {cand_name}")
                st.write(f"**Competencies:** {', '.join(skills) if skills else 'N/A'}")
            with r2:
                fig = go.Figure(data=[go.Pie(labels=['Technical', 'Soft Skills'], values=[tech_w, soft_w], hole=.4)])
                st.plotly_chart(fig, use_container_width=True)

            # Database Update
            try:
                supabase.table("candidate_results").insert({
                    "candidate_name": cand_name, "jd_role": f"{difficulty} Specialist",
                    "total_score": float(tech_w), "created_by": st.session_state.user_role
                }).execute()
            except: pass

            # PDF Download
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [Paragraph(f"INTERVIEW RUBRIC: {cand_name}", styles['Title']), Spacer(1, 20)]
            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"{i}. {q}", styles['Normal']))
            doc.build(elements)
            st.download_button("📥 Download Report", buffer.getvalue(), f"{cand_name}_Report.pdf", "application/pdf")

    elif page == "Assessment History (Admin Only)":
        if st.session_state.user_role == "Admin":
            st.header("Enterprise Audit Logs")
            res = supabase.table("candidate_results").select("*").execute()
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        else:
            st.error("🚫 Access Denied: This section is restricted to Admin accounts only.")