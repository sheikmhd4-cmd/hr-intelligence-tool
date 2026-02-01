
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

# ---------------- SESSION ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None


# ---------------- CORE ----------------
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
}


def extract_skills(text):
    found = [v for k, v in SKILL_DB.items() if k in text.lower()]
    return list(set(found))


def generate_questions(skills, level):
    qs = []
    for s in skills:
        qs.extend([
            f"Explain fundamentals of {s}.",
            f"Describe a production project using {s}.",
            f"How do you debug failures in {s} systems?",
            f"Security risks associated with {s}.",
            f"Scaling strategies for {s}.",
        ])

    if level == "Junior":
        qs.extend([
            "What technical problem did you recently solve?",
            "Explain a system you built end-to-end.",
        ])
    elif level == "Mid":
        qs.extend([
            "How do you mentor juniors?",
            "How do you design fault tolerant systems?",
        ])
    else:
        qs.extend([
            "Describe the largest system you architected.",
            "How do you evaluate trade-offs in architecture?",
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
    elif "Python" in skills:
        role = "Backend Engineer"
    else:
        role = "Software Engineer"

    focus = "Technical Heavy" if tech >= 65 else "Balanced"

    insight = (
        f"This JD focuses on {', '.join(skills)}. "
        f"Candidate should demonstrate system thinking, "
        f"problem-solving ability and leadership expected "
        f"for a {level} role."
    )

    return role, focus, insight


# ---------------- AUTH ----------------
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
                        if res.user:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.rerun()
                    except:
                        st.error("Authentication failed.")
        with reg_tab:
            with st.form("reg_form"):
                new_email = st.text_input("Email Address")
                new_pass = st.text_input("Password", type="password")
                reg = st.form_submit_button("Create Account", use_container_width=True)
                if reg:
                    try:
                        supabase.auth.sign_up({"email": new_email, "password": new_pass})
                        st.info("Registration successful.")
                    except Exception as e:
                        st.error(str(e))


# ---------------- MAIN ----------------
else:
    st.sidebar.markdown(f"### Role: {st.session_state.user_role.upper()}")
    nav = ["Framework Generator"]
    if st.session_state.user_role == "Admin":
        nav.append("Assessment History")

    page = st.sidebar.radio("Navigation", nav)

    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.session_state.user_role = None
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
            role, focus, insight = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)

            st.divider()
            r1, r2 = st.columns([1, 1])
            with r1:
                st.subheader("Live Result Summary")
                # Candidate name added to summary UI
                st.write(f"**Candidate:** {cand if cand else 'N/A'}")
                st.write(f"**Detected Skills:** {', '.join(skills)}")
                st.write(f"**Suggested Role:** {role}")
                st.write(f"**Focus Area:** {focus}")
                st.info(insight)

            with r2:
                fig = go.Figure(
                    data=[go.Pie(labels=["Technical", "Soft Skills"], values=[tech, soft], hole=0.45)]
                )
                fig.update_layout(height=380, width=380)
                st.plotly_chart(fig, use_container_width=False)

            st.markdown("### Targeted Interview Questions")
            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

           # 1. Process பட்டனுக்கு உள்ளே டேட்டாவை சேமிக்கவும்
        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            role, focus, insight = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)
            
            # இந்த Session State மிக முக்கியம் (இதுதான் PDF-ஐ பிளாங்க் ஆகாமல் தடுக்கும்)
            st.session_state.results = {
                "cand": cand, 
                "skills": skills, 
                "role": role, 
                "focus": focus, 
                "insight": insight, 
                "questions": questions,
                "tech": tech, 
                "soft": 100 - tech
            }

        # 2. முடிவுகள் இருந்தால் மட்டும் UI மற்றும் PDF டவுன்லோட் காட்டவும்
        if st.session_state.get('results'):
            res = st.session_state.results
            
            # ... (உங்களுடைய பழைய UI Summary & Pie Chart கோடுகள் இங்கே இருக்கும்) ...

            # -------- சரி செய்யப்பட்ட PDF BLOCK --------
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            elements = []
            elements.append(Paragraph("INTERVIEW ASSESSMENT REPORT", styles["Title"]))
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(f"<b>Candidate Name:</b> {res['cand'] if res['cand'] else 'N/A'}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Role:</b> {res['role']}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Skills:</b> {', '.join(res['skills'])}", styles["Normal"]))
            elements.append(Spacer(1, 15))
            elements.append(Paragraph("<b>Targeted Interview Questions:</b>", styles["Heading2"]))
            
            for i, q in enumerate(res['questions'], 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))
                elements.append(Spacer(1, 5))

            doc.build(elements)
            pdf_data = pdf_buffer.getvalue() # Buffer-ல் இருந்து டேட்டாவை எடுக்கிறோம்

            st.download_button(
                label="📥 Download Report",
                data=pdf_data,
                file_name=f"Assessment_{res['cand']}.pdf" if res['cand'] else "Assessment_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )


