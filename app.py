import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------

# Unga original Supabase details
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# ---------------- SESSION ----------------

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "results" not in st.session_state:
    st.session_state.results = None

# ---------------- CORE LOGIC ----------------

SKILL_DB = {
    "python": "Python",
    "sql": "SQL",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "react": "React",
    "machine learning": "Machine Learning",
    "data analysis": "Data Analysis",
    "devops": "DevOps",
    "ci/cd": "CI/CD",
    "terraform": "Terraform",
    "linux": "Linux",
    "java": "Java",
    "javascript": "JavaScript",
    "api": "API Development",
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

def generate_summary(skills, level, tech):
    if "Machine Learning" in skills:
        role = "Data Scientist / ML Engineer"
    elif "DevOps" in skills:
        role = "Cloud / DevOps Engineer"
    elif "React" in skills:
        role = "Frontend Engineer"
    else:
        role = "Software Engineer"

    focus = "strongly technical" if tech >= 65 else "balanced between technical and soft skills"

    paragraph = (
        f"This job description clearly targets a **{level}-level {role}** profile with "
        f"primary emphasis on **{', '.join(skills)}**. The role appears to be "
        f"{focus}, meaning the candidate will be expected to handle real-world systems, "
        f"debug production issues, and collaborate with cross-functional teams.\n\n"
        f"From a hiring perspective, this position is suitable for professionals who "
        f"have already worked on deployed projects rather than purely academic exercises. "
        f"The interview should therefore explore architectural decisions, problem-solving "
        f"approach, communication clarity, and how the candidate handles ambiguity in live systems.\n\n"
        f"Overall, the JD suggests a performance-driven role where impact, scalability, "
        f"and reliability matter more than certifications alone."
    )
    return role, paragraph

# ---------------- AUTH UI ----------------

if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align:center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        login_tab, reg_tab = st.tabs(["Secure Login", "Registration"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Corporate Email")
                password = st.text_input("Password", type="password")
                role_choice = st.selectbox("Login as", ["Admin", "User"])
                submit = st.form_submit_button("Authenticate", use_container_width=True)
                if submit:
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        if res and res.session:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.session_state.results = None
                            st.rerun()
                        else:
                            st.error("Authentication failed.")
                    except:
                        st.error("Authentication failed.")

        with reg_tab:
            with st.form("reg_form"):
                new_email = st.text_input("Email Address")
                new_pass = st.text_input("Password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pass})
                        st.info("Registration successful.")
                    except Exception as e:
                        st.error(str(e))

# ---------------- MAIN APP ----------------

else:
    st.sidebar.markdown(f"### Role: {st.session_state.user_role.upper()}")
    nav = ["Framework Generator"]
    if st.session_state.user_role == "Admin":
        nav.append("Assessment History")

    page = st.sidebar.radio("Navigation", nav, key="nav_radio")

    if st.sidebar.button("Logout Session", key="logout_btn"):
        st.session_state.auth_status = False
        st.session_state.user_role = None
        st.session_state.results = None
        st.rerun()

    if page == "Framework Generator":
        st.header("Evaluation Framework")
        c1, c2 = st.columns([1.5, 1])

        with c1:
            jd = st.text_area("Input Job Description", height=260)
        with c2:
            cand = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech = st.slider("Technical Weight (%)", 0, 100, 70)
            soft = 100 - tech

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            role, summary_para = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)
            st.session_state.results = {
                "cand": cand, "skills": skills, "role": role,
                "summary": summary_para, "questions": questions,
                "tech": tech, "soft": soft
            }

        if st.session_state.results:
            res = st.session_state.results
            st.divider()
            r1, r2 = st.columns([1, 1])

            with r1:
                st.subheader("Live Result Summary")
                st.markdown(f"""
                <div style="background-color:#0f172a;padding:18px;border-radius:12px;color:white;">
                <h4>Candidate:</h4> {res['cand'] or 'N/A'}<br><br>
                <h4>Detected Skills:</h4> {', '.join(res['skills'])}<br><br>
                <h4>Suggested Role:</h4> {res['role']}<br><br>
                <p>{res['summary']}</p>
                </div>
                """, unsafe_allow_html=True)

            with r2:
                # 1. PIE CHART (Unchanged but with better colors)
                fig = go.Figure(data=[go.Pie(
                    labels=["Technical", "Soft Skills"],
                    values=[res["tech"], res["soft"]],
                    hole=0.45,
                    marker=dict(colors=['#60a5fa', '#1d4ed8'])
                )])
                fig.update_layout(height=350, margin=dict(t=20, b=0, l=0, r=0), 
                                 paper_bgcolor='rgba(0,0,0,0)', font=dict(color="white"))
                st.plotly_chart(fig, use_container_width=True)

                # 2. INDICATOR BAR (Added to fill the empty space)
                fig_bar = go.Figure(go.Bar(
                    x=[res["tech"], res["soft"]],
                    y=["Technical  ", "Soft Skills  "],
                    orientation='h',
                    marker=dict(color=['#60a5fa', '#1d4ed8']),
                    text=[f"{res['tech']}%", f"{res['soft']}%"],
                    textposition='inside',
                    width=0.4
                ))
                fig_bar.update_layout(height=180, margin=dict(t=10, b=10, l=10, r=10),
                                     xaxis=dict(visible=False, range=[0, 100]),
                                     yaxis=dict(showgrid=False, font=dict(color="white")),
                                     paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                     showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            st.markdown("### Targeted Interview Questions")
            for i, q in enumerate(res["questions"], 1):
                st.info(f"{i}. {q}")

            # PDF Download Logic
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = [
                Paragraph("INTERVIEW ASSESSMENT REPORT", styles["Title"]),
                Spacer(1, 20),
                Paragraph(f"<b>Candidate:</b> {res['cand'] or 'N/A'}", styles["Normal"]),
                Paragraph(f"<b>Role:</b> {res['role']}", styles["Normal"]),
                Paragraph(f"<b>Skills:</b> {', '.join(res['skills'])}", styles["Normal"]),
                Spacer(1, 15),
                Paragraph("<b>Summary:</b>", styles["Heading2"]),
                Paragraph(res["summary"], styles["Normal"]),
                Spacer(1, 15),
                Paragraph("<b>Questions:</b>", styles["Heading2"]),
            ]
            for i, q in enumerate(res["questions"], 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
            doc.build(elements)

            st.download_button("📥 Download Detailed Report", pdf_buffer.getvalue(), 
                             file_name="Assessment_Report.pdf", mime="application/pdf", 
                             use_container_width=True, key="pdf_btn")