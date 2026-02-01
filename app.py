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

# ---------------- SESSION STATE ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if "user_role" not in st.session_state:
    st.session_state.user_role = None


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


def generate_summary_text(cand_name, skills, difficulty, tech_w):

    role = infer_role_from_skills(skills)

    focus = "Technical-heavy evaluation" if tech_w >= 65 else "Balanced evaluation"

    note = (
        f"This job description emphasizes {', '.join(skills)}. "
        f"The candidate should be evaluated for architecture design, debugging depth, "
        f"problem-solving ability, and communication skills suitable for a {difficulty}-level role."
    )

    return {
        "role": role,
        "focus": focus,
        "note": note,
        "count": len(skills),
    }


def generate_questions(skills, level):

    qs = []

    for s in skills:
        qs.extend(
            [
                f"Explain core concepts of {s}.",
                f"Real-world project where you used {s}.",
                f"Debugging challenges faced in {s}.",
                f"Performance optimization in {s}.",
                f"Security or reliability concerns in {s}.",
            ]
        )

    # Level-based bonus questions
    if level == "Junior":
        qs.append("Explain a recent technical problem you solved.")
    elif level == "Mid":
        qs.append("How do you mentor juniors or review code?")
    else:
        qs.append("Describe architectural decisions you led.")

    return qs[:12]


# ---------------- AUTH UI ----------------
if not st.session_state.auth_status:

    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:

        st.markdown(
            "<h1 style='text-align: center;'>HR Intelligence Portal</h1>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        login_tab, reg_tab = st.tabs(["Secure Login", "Registration"])

        with login_tab:

            with st.form("login_form"):

                email = st.text_input("Corporate Email")
                password = st.text_input("Password", type="password")
                role_choice = st.selectbox("Login as", ["Admin", "User"])

                submit_button = st.form_submit_button(
                    "Authenticate", use_container_width=True
                )

                if submit_button:
                    try:
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )

                        if res.user:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.rerun()

                    except:
                        st.error("Authentication failed. Please check credentials.")

        with reg_tab:

            with st.form("reg_form"):

                new_email = st.text_input("Email Address")
                new_pass = st.text_input("Set Password", type="password")

                reg_button = st.form_submit_button(
                    "Create Account", use_container_width=True
                )

                if reg_button:
                    try:
                        supabase.auth.sign_up(
                            {"email": new_email, "password": new_pass}
                        )

                        st.info(
                            "Registration request sent. Please check email or login."
                        )

                    except Exception as e:
                        st.error(str(e))


# ---------------- MAIN APP ----------------
else:

    st.sidebar.markdown(f"### Role: **{st.session_state.user_role.upper()}**")
    st.sidebar.divider()

    nav_options = ["Framework Generator"]

    if st.session_state.user_role == "Admin":
        nav_options.append("Assessment History")

    page = st.sidebar.radio("Navigation", nav_options)

    if st.sidebar.button("Logout Session", use_container_width=True):
        st.session_state.auth_status = False
        st.session_state.user_role = None
        st.rerun()

    # ------------- FRAMEWORK PAGE -------------
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

            summary = generate_summary_text(
                cand_name, skills, difficulty, tech_w
            )

            questions = generate_questions(skills, difficulty)

            st.divider()

            r1, r2 = st.columns([1, 1])

            with r1:

                st.subheader("Live Result Summary")

                st.write(f"**Candidate:** {cand_name or 'N/A'}")
                st.write(f"**Detected Skills:** {', '.join(skills) or 'None'}")
                st.write(f"**Skill Count:** {summary['count']}")
                st.write(f"**Suggested Role:** {summary['role']}")
                st.write(f"**Focus Area:** {summary['focus']}")

                st.info(summary["note"])

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

                fig.update_layout(height=240)
                st.plotly_chart(fig, use_container_width=True)

            # ---------- QUESTIONS ----------
            st.markdown("### Targeted Interview Questions")

            for i, q in enumerate(questions, 1):
                st.info(f"{i}. {q}")

            # ---------- DB SAVE ----------
            try:
                supabase.table("candidate_results").insert(
                    {
                        "candidate_name": cand_name,
                        "jd_role": summary["role"],
                        "total_score": float(tech_w),
                        "created_by": st.session_state.user_role,
                    }
                ).execute()

            except:
                pass

            # ---------- PDF ----------
            buffer = io.BytesIO()

            doc = SimpleDocTemplate(buffer, pagesize=A4)

            styles = getSampleStyleSheet()

            elements = []

            elements.append(
                Paragraph(f"INTERVIEW REPORT – {cand_name}", styles["Title"])
            )

            elements.append(Spacer(1, 20))

            elements.append(
                Paragraph(
                    f"<b>Detected Skills:</b> {', '.join(skills)}",
                    styles["Normal"],
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Suggested Role:</b> {summary['role']}",
                    styles["Normal"],
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Focus Area:</b> {summary['focus']}",
                    styles["Normal"],
                )
            )

            elements.append(
                Paragraph(
                    f"<b>Assessment Insight:</b> {summary['note']}",
                    styles["Normal"],
                )
            )

            elements.append(Spacer(1, 20))

            for i, q in enumerate(questions, 1):
                elements.append(
                    Paragraph(f"{i}. {q}", styles["Normal"])
                )

            doc.build(elements)

            st.download_button(
                "📥 Download Report",
                buffer.getvalue(),
                f"{cand_name}_Assessment.pdf",
                "application/pdf",
            )

    # ------------- HISTORY PAGE -------------
    elif page == "Assessment History":

        st.header("Enterprise Audit Logs")

        res = supabase.table("candidate_results").select("*").execute()

        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
