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

# ---------------- AUTH UI ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        st.markdown("---")
        tabs = st.tabs(["Secure Login", "Registration"])
        
        with tabs[0]:
            email = st.text_input("Corporate Email")
            password = st.text_input("Password", type="password")
            # --- Role Selection Added Back ---
            user_role = st.selectbox("Select Role", ["Admin", "User"]) 
            if st.button("Authenticate", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.auth_status = True
                    st.session_state.user_role = user_role
                    st.rerun()
                except:
                    st.error("Authentication failed. Please check credentials.")

        with tabs[1]:
            new_email = st.text_input("Email Address")
            new_pass = st.text_input("Set Password", type="password")
            if st.button("Create Account", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pass})
                    st.info("Registration request sent. Please attempt login.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# ---------------- MAIN APP ----------------
else:
    # --- Sidebar with Role & Logout ---
    st.sidebar.markdown(f"### Access Level: **{st.session_state.user_role.upper()}**")
    st.sidebar.divider()
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment History"])
    
    st.sidebar.divider()
    # --- Logout Button Added Back ---
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
            
            # --- Result UI with Pie Chart ---
            st.divider()
            r1, r2 = st.columns([1, 1])
            with r1:
                st.subheader("Summary")
                st.write(f"**Name:** {cand_name}")
                st.write(f"**Competencies:** {', '.join(skills) if skills else 'N/A'}")
                st.write(f"**Seniority:** {difficulty}")
            
            with r2:
                # Plotly Pie Chart Visualization
                fig = go.Figure(data=[go.Pie(
                    labels=['Technical', 'Soft Skills'], 
                    values=[tech_w, soft_w],
                    hole=.4,
                    marker_colors=['#1E3A8A', '#94A3B8']
                )])
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200)
                st.plotly_chart(fig, use_container_width=True)

            # Questions Display
            st.markdown("### Targeted Questions")
            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

            # Database Update
            try:
                supabase.table("candidate_results").insert({
                    "candidate_name": cand_name, "jd_role": f"{difficulty} Specialist",
                    "total_score": float(tech_w), "created_by": st.session_state.user_role
                }).execute()
            except: pass

            # --- Professional PDF ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph(f"INTERVIEW RUBRIC: {cand_name}", styles['Title']),
                HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=20),
                Table([["Level:", difficulty], ["Tech Weight:", f"{tech_w}%"], ["Soft Skills:", f"{soft_w}%"]], 
                      style=TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)])),
                Spacer(1, 20),
                Paragraph("<b>Interview Questions:</b>", styles['Heading3'])
            ]
            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"{i}. {q}", styles['Normal']))
            
            doc.build(elements)
            st.download_button("📥 Download Report", buffer.getvalue(), f"{cand_name}_Report.pdf", "application/pdf", use_container_width=True)

    elif page == "Assessment History":
        st.header("Enterprise Logs")
        res = supabase.table("candidate_results").select("*").execute()
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)