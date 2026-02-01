import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

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


def infer_role_from_skills(skills):

    if "Machine Learning" in skills and "Data Analysis" in skills:
        return "Data Scientist / ML Engineer"

    if "AWS" in skills and "DevOps" in skills:
        return "Cloud / DevOps Engineer"

    if "React" in skills:
        return "Frontend Engineer"

    if "Python" in skills and "SQL" in skills:
        return "Backend Engineer"

    return "Software Engineer"


def generate_summary(cand, skills, level, tech_w):

    role = infer_role_from_skills(skills)

    focus = "Technical Heavy" if tech_w >= 65 else "Balanced"

    note = (
        f"This JD strongly focuses on {', '.join(skills)}. "
        f"Candidate should demonstrate architecture reasoning, debugging ability, "
        f"scalability thinking and communication expected for {level} role."
    )

    return role, focus, note


def generate_questions(skills, level):

    qs = []

    for s in skills:
        qs.extend(
            [
                f"Explain fundamentals of {s}.",
                f"Describe a real project using {s}.",
                f"Performance tuning in {s}.",
                f"Security risks in {s}.",
                f"Scaling challenges with {s}.",
            ]
        )

    if level == "Junior":
        qs.append("What technical problem did you recently solve?")
    elif level == "Mid":
        qs.append("How do you mentor juniors?")
    else:
        qs.append("Describe architecture you designed.")

    return qs[:12]


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

    # -------- FRAMEWORK --------
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

            role, focus, note = generate_summary(cand, skills, level, tech)

            questions = generate_questions(skills, level)

            st.divider()

            r1, r2 = st.columns([1, 1])

            with r1:

                st.subheader("Live Result Summary")

                st.write(f"**Candidate:** {cand}")
                st.write(f"**Detected Skills:** {', '.join(skills)}")
                st.write(f"**Suggested Role:** {role}")
                st.write(f"**Focus Area:** {focus}")

                st.info(note)

            with r2:

                fig = go.Figure(
                    data=[go.Pie(labels=["Technical", "Soft Skills"], values=[tech, soft], hole=0.45)]
                )

                fig.update_layout(height=360, width=360)

                st.plotly_chart(fig, use_container_width=False)

            # -------- QUESTIONS --------
            st.markdown("### Targeted Interview Questions")

            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

            # -------- PDF --------
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=A4)

            styles = getSampleStyleSheet()

            elements = []

            elements.append(Paragraph(f"INTERVIEW REPORT – {cand}", styles["Title"]))
            elements.append(Spacer(1, 20))

            elements.append(Paragraph(f"<b>Detected Skills:</b> {', '.join(skills)}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Suggested Role:</b> {role}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Focus Area:</b> {focus}", styles["Normal"]))
            elements.append(Paragraph(f"<b>Assessment Insight:</b> {note}", styles["Normal"]))

            elements.append(Spacer(1, 20))

            for i, q in enumerate(questions, 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))

            doc.build(elements)

            buffer.seek(0)   # 🔥 IMPORTANT FIX

            st.download_button(
                "📥 Download Report",
                buffer,
                file_name=f"{cand}_Assessment.pdf",
                mime="application/pdf",
            )

    # -------- HISTORY --------
    elif page == "Assessment History":

        st.header("Enterprise Audit Logs")

        res = supabase.table("candidate_results").select("*").execute()

        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
