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
if "results" not in st.session_state:
    st.session_state.results = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker",
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "Machine Learning",
    "data analysis": "Data Analysis", "devops": "DevOps",
    "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
    "java": "Java", "javascript": "JavaScript", "api": "API Development"
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
    while len(qs) < 12:
        qs.append("Explain a complex technical challenge you solved recently.")
    return qs[:12]

def generate_hiring_intelligence(skills, level, tech):
    risks = []
    signals = []
    focus = []
    gaps = []

    if "General Technical" in skills:
        risks.append("JD is vague on technical depth.")
        gaps.append("Role clarity missing in JD.")

    if tech >= 70:
        focus.append("Deep system design and architecture.")
    else:
        focus.append("Behavioral + collaboration scenarios.")

    if "DevOps" in skills:
        signals.append("Production reliability exposure expected.")
        focus.append("Incident handling and scaling.")
    if "Machine Learning" in skills:
        signals.append("Model lifecycle ownership.")
        focus.append("Data pipelines and evaluation metrics.")

    seniority = "High confidence for senior role." if level == "Senior" else "Moderate maturity expected."

    recommendation = (
        "Strong hire if candidate demonstrates ownership and production impact."
        if tech >= 65 else
        "Hire depends on collaboration and learning agility."
    )

    return {
        "risks": risks or ["No major risk flags detected."],
        "signals": signals or ["Generalist engineering exposure expected."],
        "focus": focus,
        "gaps": gaps or ["JD appears balanced."],
        "seniority": seniority,
        "recommendation": recommendation
    }

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
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
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

                if st.form_submit_button("Create Account", use_container_width=True):
                    try:
                        supabase.auth.sign_up(
                            {"email": new_email, "password": new_pass}
                        )
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

    if st.sidebar.button("Logout Session"):
        st.session_state.auth_status = False
        st.session_state.results = None
        st.rerun()

    if page == "Framework Generator":

        st.header("Evaluation Framework")

        c1, c2 = st.columns([1.5, 1])
        with c1:
            jd = st.text_area("Input Job Description", height=260)

        with c2:
            cand = st.text_input("Candidate Name", value="")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech = st.slider("Technical Weight (%)", 0, 100, 70)
            soft = 100 - tech

        if st.button("Process Assessment", use_container_width=True) and jd:

            skills = extract_skills(jd)
            questions = generate_questions(skills, level)
            intelligence = generate_hiring_intelligence(skills, level, tech)

            st.session_state.results = {
                "cand": cand,
                "skills": skills,
                "questions": questions,
                "tech": tech,
                "soft": soft,
                **intelligence
            }

        if st.session_state.results:

            res = st.session_state.results

            st.divider()

            r1, r2 = st.columns([1, 1])

            with r1:
                st.subheader("Live Result Summary")

                st.write(f"**Candidate:** {res['cand'] or 'N/A'}")
                st.write(f"**Detected Skills:** {', '.join(res['skills'])}")

                st.markdown("### 🧠 Hiring Intelligence")

                st.markdown("**⚠ Risk Flags:**")
                for x in res["risks"]:
                    st.write("- " + x)

                st.markdown("**✅ Hiring Signals:**")
                for x in res["signals"]:
                    st.write("- " + x)

                st.markdown("**🎯 Interview Focus Areas:**")
                for x in res["focus"]:
                    st.write("- " + x)

                st.markdown("**📉 JD Gaps:**")
                for x in res["gaps"]:
                    st.write("- " + x)

                st.markdown(f"**📊 Seniority Confidence:** {res['seniority']}")
                st.success(res["recommendation"])

            with r2:
                fig = go.Figure(
                    data=[go.Pie(
                        labels=["Technical", "Soft Skills"],
                        values=[res["tech"], res["soft"]],
                        hole=0.45
                    )]
                )

                fig.update_layout(height=350, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Targeted Interview Questions")

            for i, q in enumerate(res["questions"], 1):
                st.info(f"{i}. {q}")

            # -------- PDF --------
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()

            elements = [
                Paragraph("INTERVIEW ASSESSMENT REPORT", styles["Title"]),
                Spacer(1, 20),
                Paragraph(f"<b>Candidate:</b> {res['cand'] or 'N/A'}", styles["Normal"]),
                Paragraph(f"<b>Skills:</b> {', '.join(res['skills'])}", styles["Normal"]),
                Spacer(1, 15),
                Paragraph("<b>Risk Flags</b>", styles["Heading2"])
            ]

            for x in res["risks"]:
                elements.append(Paragraph(f"- {x}", styles["Normal"]))

            elements.append(Spacer(1, 12))
            elements.append(Paragraph("<b>Hiring Recommendation</b>", styles["Heading2"]))
            elements.append(Paragraph(res["recommendation"], styles["Normal"]))

            for i, q in enumerate(res["questions"], 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))

            doc.build(elements)

            st.download_button(
                "📥 Download Detailed Report",
                pdf_buffer.getvalue(),
                file_name="Assessment_Report.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

    elif page == "Assessment History":

        st.header("Enterprise Audit Logs")

        try:
            res_db = supabase.table("candidate_results").select("*").execute()
            st.dataframe(pd.DataFrame(res_db.data), use_container_width=True)
        except:
            st.error("Database connection error.")
