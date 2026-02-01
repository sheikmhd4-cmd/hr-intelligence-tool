import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ---------------- #

SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# ---------------- SESSION ---------------- #

if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ---------------- SKILLS ---------------- #

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

QUESTION_BANK = {
    "Python": [
        "Explain list vs tuple with real use cases.",
        "What is GIL in Python?",
        "How memory is managed?",
        "Decorators — explain with example.",
        "Difference between shallow and deep copy?",
        "How do generators work?",
        "Explain multiprocessing vs threading.",
        "How exceptions propagate?",
        "What are context managers?",
        "How Python handles async IO?",
    ],
    "SQL": [
        "Difference between WHERE and HAVING?",
        "Explain indexing.",
        "Normalize a table.",
        "Write a JOIN query.",
        "Primary vs Foreign key?",
        "Clustered index?",
        "Subqueries vs CTE?",
        "ACID properties?",
        "Query optimization?",
        "Window functions?",
    ],
}

# ---------------- CORE LOGIC ---------------- #

def extract_skills(text: str):
    found = []
    for k, v in SKILL_DB.items():
        if k in text.lower():
            found.append(v)

    return list(set(found))


def generate_questions(skills, level):
    questions = []

    for skill in skills:
        base = QUESTION_BANK.get(skill, [])

        for q in base:
            if level == "Junior":
                questions.append(f"[{skill}] Basics — {q}")
            elif level == "Mid":
                questions.append(f"[{skill}] Implementation — {q}")
            else:
                questions.append(f"[{skill}] Architecture — {q}")

    # 🔥 ENSURE MIN 10 QUESTIONS
    while len(questions) < 10:
        questions.append(
            "General: Explain a challenging technical problem you solved recently."
        )

    return questions[:15]

# ---------------- AUTH ---------------- #

if not st.session_state.auth_status:

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        st.markdown("<h1 style='text-align:center'>HR Intelligence Portal</h1>", unsafe_allow_html=True)

        login_tab, reg_tab = st.tabs(["Secure Login", "Registration"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Corporate Email")
                password = st.text_input("Password", type="password")
                role_choice = st.selectbox("Login as", ["Admin", "User"])

                submit = st.form_submit_button("Authenticate", use_container_width=True)

                if submit:
                    try:
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )

                        if res.user:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.rerun()

                    except:
                        st.error("Authentication failed")

        with reg_tab:
            with st.form("reg_form"):
                new_email = st.text_input("Email Address")
                new_pass = st.text_input("Set Password", type="password")

                reg_btn = st.form_submit_button("Create Account", use_container_width=True)

                if reg_btn:
                    try:
                        supabase.auth.sign_up(
                            {"email": new_email, "password": new_pass}
                        )
                        st.success("Registered. Check email.")
                    except:
                        st.error("Registration failed")

# ---------------- MAIN APP ---------------- #

else:

    st.sidebar.markdown(f"### Role: {st.session_state.user_role.upper()}")
    st.sidebar.divider()

    nav = ["Framework Generator"]

    if st.session_state.user_role == "Admin":
        nav.append("Assessment History")

    page = st.sidebar.radio("Navigation", nav)

    if st.sidebar.button("Logout Session", use_container_width=True):
        st.session_state.auth_status = False
        st.session_state.user_role = None
        st.rerun()

    # -------- FRAMEWORK -------- #

    if page == "Framework Generator":

        st.header("Evaluation Framework")

        col_jd, col_p = st.columns([1.5, 1])

        with col_jd:
            jd = st.text_area("Input Job Description", height=250)

        with col_p:
            cand_name = st.text_input("Candidate Name")
            difficulty = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weight (%)", 0, 100, 70)

        soft_w = 100 - tech_w

        if st.button("Process Assessment", use_container_width=True) and jd:

            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)

            st.divider()

            r1, r2 = st.columns(2)

            with r1:
                st.subheader("Live Result Summary")
                st.write(f"**Candidate:** {cand_name}")
                st.write(f"**Competencies:** {', '.join(skills) if skills else 'N/A'}")

            with r2:
                fig = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Technical", "Soft Skills"],
                            values=[tech_w, soft_w],
                            hole=0.4,
                        )
                    ]
                )

                fig.update_layout(height=220, margin=dict(t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 🎯 Targeted Questions")

            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

            # -------- SAVE DB -------- #

            try:
                supabase.table("candidate_results").insert(
                    {
                        "candidate_name": cand_name,
                        "jd_role": f"{difficulty} Role",
                        "total_score": tech_w,
                        "created_by": st.session_state.user_role,
                    }
                ).execute()
            except:
                pass

            # -------- PDF -------- #

            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()

            elements = [
                Paragraph(f"INTERVIEW REPORT — {cand_name}", styles["Title"]),
                Spacer(1, 20),
            ]

            for q in questions:
                elements.append(Paragraph(q, styles["Normal"]))

            doc.build(elements)
            buffer.seek(0)

            st.download_button(
                "📥 Download Report",
                buffer,
                f"{cand_name}_Report.pdf",
                "application/pdf",
            )

    # -------- HISTORY -------- #

    elif page == "Assessment History":

        st.header("Enterprise Audit Logs")

        res = supabase.table("candidate_results").select("*").execute()

        if res.data:
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        else:
            st.info("No data found yet.")
