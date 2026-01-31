import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="HR Prompt Engineering Tool",
    layout="wide",
    page_icon="💼"
)

# ---------- TITLE ----------
st.title("HR Prompt Engineering Tool")
st.markdown("**Convert Job Descriptions into Interview Frameworks with Assessment & Scoring**")

# ---------- JOB DESCRIPTION ----------
uploaded_file = st.file_uploader("Upload Job Description (.txt only)", type=["txt"])
if uploaded_file is not None:
    jd = uploaded_file.read().decode("utf-8")
else:
    jd = st.text_area("Or Paste Job Description Here", height=200)

# ---------- SAMPLE QUESTIONS & TASKS ----------
tech_qs = [
    "Explain CI/CD pipelines and their importance.",
    "How would you deploy a Python application using Docker?",
    "What is Kubernetes and where have you used it?",
    "Explain rollback strategies in deployments.",
    "How do you monitor production systems?"
]

behav_qs = [
    "Describe a time you solved a complex technical problem.",
    "How do you handle tight deadlines?",
    "Tell us about a conflict within your team.",
    "How do you learn new technologies quickly?",
    "Describe a failure and what you learned from it."
]

tasks = [
    "Build a simple CI/CD pipeline for a Python application.",
    "Deploy an application using Docker and Kubernetes.",
    "Write a system design document for scalable deployment."
]

# ---------- INTERACTIVE RUBRIC ----------
st.markdown("<h3 style='color:#D35400;'>Scoring Rubric (Editable)</h3>", unsafe_allow_html=True)
technical_weight = st.slider("Technical Skill (%)", 0, 100, 40)
problem_solving_weight = st.slider("Problem Solving (%)", 0, 100, 25)
system_design_weight = st.slider("System Design (%)", 0, 100, 20)
communication_weight = st.slider("Communication (%)", 0, 100, 15)

rubric = {
    "Technical Skill": technical_weight,
    "Problem Solving": problem_solving_weight,
    "System Design": system_design_weight,
    "Communication": communication_weight
}

# ---------- GENERATE FRAMEWORK ----------
if st.button("Generate Interview Framework"):

    # ---------- LAYOUT ----------
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<h3 style='color:#0B5345;'>Technical Questions</h3>", unsafe_allow_html=True)
        for q in tech_qs:
            st.write("•", q)

        st.markdown("<h3 style='color:#154360;'>Behavioral Questions</h3>", unsafe_allow_html=True)
        for q in behav_qs:
            st.write("•", q)

        st.markdown("<h3 style='color:#7D3C98;'>Assessment Tasks</h3>", unsafe_allow_html=True)
        for t in tasks:
            st.write("•", t)

    with col2:
        st.markdown("<h3 style='color:#D35400;'>Scoring Rubric Visualization</h3>", unsafe_allow_html=True)
        df_rubric = pd.DataFrame(list(rubric.items()), columns=["Criteria", "Weight"])
        st.table(df_rubric)

        chart = alt.Chart(df_rubric).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Weight", type="quantitative"),
            color=alt.Color(field="Criteria", type="nominal"),
            tooltip=["Criteria", "Weight"]
        )
        st.altair_chart(chart, use_container_width=True)

    # ---------- PDF REPORT ----------
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "HR Prompt Engineering Tool Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 8, f"JOB DESCRIPTION:\n{jd}")
    pdf.ln(5)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Technical Questions:", ln=True)
    pdf.set_font("Arial", '', 12)
    for q in tech_qs:
        pdf.multi_cell(0, 8, f"- {q}")
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Behavioral Questions:", ln=True)
    pdf.set_font("Arial", '', 12)
    for q in behav_qs:
        pdf.multi_cell(0, 8, f"- {q}")
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Assessment Tasks:", ln=True)
    pdf.set_font("Arial", '', 12)
    for t in tasks:
        pdf.multi_cell(0, 8, f"- {t}")
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, "Scoring Rubric:", ln=True)
    pdf.set_font("Arial", '', 12)
    for k, v in rubric.items():
        pdf.cell(0, 8, f"{k}: {v}%", ln=True)

    pdf_bytes = pdf.output(dest='S').encode('latin1')

    st.download_button(
        label="Download PDF Report",
        data=pdf_bytes,
        file_name="hr_report.pdf",
        mime="application/pdf"
    )

    st.success("PDF report ready! Download to showcase professionally.")
