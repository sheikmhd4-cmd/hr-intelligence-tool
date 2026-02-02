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

# ---------- SMART SKILL EXTRACTION ----------

def extract_skills(text):
    text = text.lower()
    found = []

    for k, v in SKILL_DB.items():
        if k in text:
            found.append(v)

    # heuristic enrichment
    if "backend" in text:
        found.append("Backend Systems")
    if "frontend" in text or "ui" in text:
        found.append("Frontend Development")
    if "microservice" in text:
        found.append("Microservices")
    if "cloud" in text:
        found.append("Cloud Architecture")
    if "pipeline" in text:
        found.append("CI/CD")

    return list(set(found)) if found else ["General Engineering"]

# ---------- QUESTIONS ----------

def generate_questions(skills, level):
    qs = []

    for s in skills:
        qs.extend([
            f"What real-world systems have you built using {s}?",
            f"Explain a production issue you debugged in {s}.",
            f"How would you scale a platform built with {s}?",
        ])

    while len(qs) < 12:
        qs.append("Describe the toughest technical challenge you solved recently.")

    return qs[:12]

# ---------- SUMMARY ----------

def generate_summary(skills, level, tech):
    if "Machine Learning" in skills:
        role = "Data Scientist / ML Engineer"
    elif "DevOps" in skills or "Cloud Architecture" in skills:
        role = "Cloud / DevOps Engineer"
    elif "Frontend Development" in skills or "React" in skills:
        role = "Frontend Engineer"
    elif "Backend Systems" in skills:
        role = "Backend Engineer"
    else:
        role = "Software Engineer"

    focus = "deep technical ownership" if tech > 65 else "balanced engineering maturity"

    paragraph = (
        f"This job description targets a **{level}-level {role}** profile with strong "
        f"emphasis on **{', '.join(skills)}**. The role appears to demand "
        f"{focus}, production debugging skills, system scalability thinking, and "
        f"cross-team collaboration in real delivery environments."
    )

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
                        res = supabase.auth.sign_in_with_password(
                            {"email": email, "password": password}
                        )
                        if res and res.session:
                            st.session_state.auth_status = True
                            st.session_state.user_role = role_choice
                            st.rerun()
                        else:
                            st.error("Authentication failed.")
                    except Exception:
                        st.error("Login error.")

        with reg_tab:
            with st.form("reg_form"):
                n_email = st.text_input("Email")
                n_pass = st.text_input("Password")
                if st.form_submit_button("Create"):
                    try:
                        supabase.auth.sign_up(
                            {"email": n_email, "password": n_pass}
                        )
                        st.info("Account created.")
                    except Exception as e:
                        st.error(str(e))

# ---------------- MAIN APP ----------------

else:
    st.sidebar.markdown(
        f"### SkillSense AI\n**Role: {st.session_state.user_role.upper()}**"
    )

    nav = ["Framework Generator"]
    if st.session_state.user_role == "Admin":
        nav.append("Assessment History")

    page = st.sidebar.radio("Navigation", nav)

    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.rerun()

    # ---------- FRAMEWORK ----------

    if page == "Framework Generator":
        st.header("Evaluation Framework")

        c1, c2 = st.columns([1.5, 1])
        with c1:
            jd = st.text_area("Input Job Description", height=260)

        with c2:
            cand = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            tech = st.slider("Tech Weight (%)", 0, 100, 70)
            soft = 100 - tech

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            role, summary_para = generate_summary(skills, level, tech)
            questions = generate_questions(skills, level)

            st.session_state.results = {
                "cand": cand,
                "skills": skills,
                "role": role,
                "summary": summary_para,
                "questions": questions,
                "tech": tech,
                "soft": soft,
            }

            try:
                supabase.table("assessments").insert(
                    {
                        "candidate_name": cand,
                        "role": role,
                        "tech_score": tech,
                        "soft_score": soft,
                        "created_at": datetime.now().isoformat(),
                    }
                ).execute()
            except:
                st.warning("DB save skipped (table missing).")

        # ---------- RESULTS ----------

        if st.session_state.results:
            res = st.session_state.results

            st.divider()
            r1, r2 = st.columns([1, 1])

            with r1:
                st.subheader("Live Result Summary")
                st.markdown(
                    f"""
                    <div style='background-color:#0f172a;padding:18px;border-radius:12px;color:white;'>
                    <h4>Candidate:</h4> {res['cand'] or 'N/A'}
                    <br><h4>Role:</h4> {res['role']}
                    <br><p>{res['summary']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with r2:
                fig_pie = go.Figure(
                    data=[
                        go.Pie(
                            labels=["Technical", "Soft Skills"],
                            values=[res["tech"], res["soft"]],
                            hole=0.45,
                        )
                    ]
                )
                fig_pie.update_layout(height=300)
                st.plotly_chart(fig_pie, use_container_width=True)

                metrics_data = {
                    "Domain Fit": 85,
                    "Tech Score": res["tech"],
                    "Culture Fit": 80,
                }

                fig_metrics = go.Figure(
                    go.Bar(
                        x=list(metrics_data.values()),
                        y=list(metrics_data.keys()),
                        orientation="h",
                        text=[f"{v}%" for v in metrics_data.values()],
                        textposition="auto",
                    )
                )

                fig_metrics.update_layout(height=200, xaxis=dict(range=[0, 100]))
                st.plotly_chart(fig_metrics, use_container_width=True)

            # ---------- PDF ----------

            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            styles = getSampleStyleSheet()

            elements = [
                Paragraph(
                    f"SkillSense AI Assessment — {res['cand']}", styles["Title"]
                ),
                Spacer(1, 14),
                Paragraph("<b>Summary</b>", styles["Heading2"]),
                Paragraph(res["summary"], styles["Normal"]),
                Spacer(1, 14),
                Paragraph("<b>Targeted Interview Questions</b>", styles["Heading2"]),
            ]

            for i, q in enumerate(res["questions"], 1):
                elements.append(Paragraph(f"{i}. {q}", styles["Normal"]))

            doc.build(elements)

            st.download_button(
                "📥 Download PDF Report",
                pdf_buffer.getvalue(),
                file_name="Report.pdf",
                use_container_width=True,
            )

    # ---------- HISTORY ----------

    elif page == "Assessment History":
        st.header("Real-Time Assessment History")

        try:
            db_res = (
                supabase.table("assessments")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )

            if db_res.data:
                df = pd.DataFrame(db_res.data)
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No records found.")

        except:
            st.error("Table 'assessments' not found in Supabase.")
