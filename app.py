import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="SkillSense AI", layout="wide")

# ---------------- SESSION ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "results" not in st.session_state:
    st.session_state.results = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", "kubernetes": "Kubernetes",
    "aws": "AWS", "azure": "Azure", "react": "React", "machine learning": "Machine Learning",
    "data analysis": "Data Analysis", "devops": "DevOps", "ci/cd": "CI/CD",
    "terraform": "Terraform", "linux": "Linux", "java": "Java",
    "javascript": "JavaScript", "api": "API Development",
}

def extract_skills(text):
    text = text.lower()
    found = [v for k, v in SKILL_DB.items() if k in text]
    return list(set(found)) if found else ["General Technical"]

def generate_questions(skills, level):
    qs = []
    for s in skills:
        qs.extend([f"Explain fundamentals of {s}.", f"Describe a project using {s}.", f"How do you debug {s} systems?"])
    while len(qs) < 10: qs.append("Explain a complex technical challenge you solved.")
    return qs[:12]

def generate_summary(skills, level, tech):
    if "Machine Learning" in skills: role = "Data Scientist / ML Engineer"
    elif "DevOps" in skills: role = "Cloud / DevOps Engineer"
    elif "React" in skills: role = "Frontend Engineer"
    else: role = "Software Engineer"
    
    paragraph = f"Targeting a **{level}-level {role}** profile focusing on **{', '.join(skills)}**. Expected match: {tech}%."
    return role, paragraph

# ---------------- AUTH UI ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>SkillSense AI</h1>", unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["Secure Login", "Registration"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                role_choice = st.selectbox("Login as", ["Admin", "User"])
                if st.form_submit_button("Authenticate", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res and res.session:
                            st.session_state.auth_status, st.session_state.user_role = True, role_choice
                            st.rerun()
                        else: st.error("Failed.")
                    except: st.error("Error.")
        with reg_tab:
            with st.form("reg_form"):
                n_email, n_pass = st.text_input("Email"), st.text_input("Password")
                if st.form_submit_button("Create"):
                    try: supabase.auth.sign_up({"email": n_email, "password": n_pass}); st.info("Done.")
                    except Exception as e: st.error(str(e))

# ---------------- MAIN APP ----------------
else:
    st.sidebar.markdown(f"### SkillSense AI\n**Role: {st.session_state.user_role.upper()}**")
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
            tech = st.slider("Tech Weight (%)", 0, 100, 70)
            soft = 100 - tech

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            role, summary_para = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)
            st.session_state.results = {"cand": cand, "skills": skills, "role": role, "summary": summary_para, "questions": questions, "tech": tech, "soft": soft}
            
            # --- REAL DB SAVE (with error check) ---
            try:
                supabase.table("assessments").insert({
                    "candidate_name": cand, "role": role, "tech_score": tech, "soft_score": soft, "created_at": datetime.now().isoformat()
                }).execute()
            except Exception as e:
                st.warning(f"Note: Result not saved to DB (Table 'assessments' not found).")

        if st.session_state.results:
            res = st.session_state.results
            st.divider()
            r1, r2 = st.columns([1, 1])
            with r1:
                st.subheader("Live Result Summary")
                st.markdown(f"<div style='background-color:#0f172a;padding:18px;border-radius:12px;color:white;'><h4>Candidate:</h4> {res['cand'] or 'N/A'}<br><h4>Role:</h4> {res['role']}<br><p>{res['summary']}</p></div>", unsafe_allow_html=True)
            with r2:
                fig_pie = go.Figure(data=[go.Pie(labels=["Technical", "Soft Skills"], values=[res["tech"], res["soft"]], hole=0.45, marker=dict(colors=['#60a5fa', '#1d4ed8']))])
                fig_pie.update_layout(height=300, margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), showlegend=True, legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center"))
                st.plotly_chart(fig_pie, use_container_width=True)
                
                metrics_data = {"Domain Fit": 85, "Tech Score": res["tech"], "Culture Fit": 80}
                fig_metrics = go.Figure(go.Bar(x=list(metrics_data.values()), y=list(metrics_data.keys()), orientation='h', marker=dict(color=['#60a5fa', '#1d4ed8', '#60a5fa']), text=[f"{v}%" for v in metrics_data.values()], textposition='auto'))
                fig_metrics.update_layout(height=200, margin=dict(t=20, b=10, l=10, r=10), xaxis=dict(visible=False), yaxis=dict(showgrid=False, tickfont=dict(color="white")), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_metrics, use_container_width=True)

            # --- PDF DOWNLOAD IS HERE ---
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [Paragraph(f"SkillSense AI: {res['cand']}", styles["Title"]), Spacer(1, 12)]
            for i, q in enumerate(res["questions"], 1): elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
            doc.build(elements)
            st.download_button("📥 Download PDF Report", pdf_buffer.getvalue(), file_name="Report.pdf", use_container_width=True)

    elif page == "Assessment History":
        st.header("Real-Time Assessment History")
        try:
            # Check if assessments table exists
            db_res = supabase.table("assessments").select("*").order("created_at", desc=True).execute()
            if db_res.data:
                df = pd.DataFrame(db_res.data)
                st.dataframe(df, use_container_width=True)
            else: st.warning("No records found.")
        except Exception as e:
            st.error(f"Database Error: Could not find table 'assessments'. Please create it in Supabase.")