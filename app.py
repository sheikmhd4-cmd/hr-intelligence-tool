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
st.markdown("Convert Job Descriptions into Interview Frameworks with Assessment & Scoring")

# ---------- JOB DESCRIPTION ----------
uploaded_file = st.file_uploader("Upload Job Description (.txt only)", type=["txt"])

if uploaded_file is not None:
    jd = uploaded_file.read().decode("utf-8")
else:
    jd = st.text_area("Or Paste Job Description Here", height=200)

# ---------- SAMPLE QUESTIONS ----------
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

# ---------- RUBRIC ----------
st.subheader("Scoring Rubric (Editable)")

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

# ---------- GENERATE ----------
if st.button("Generate Interview Framework"):

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Technical Questions")
        for q in tech_qs:
            st.write("•", q)

        st.subheader("Behavioral Questions")
        for q in behav_qs:
            st.write("•", q)

        st.subheader("Assessment Tasks")
        for t in tasks:
            st.write("•", t)

    with col2:
        df = pd.DataFrame(rubric.items(), columns=["Criteria", "Weight"])
        st.table(df)

        chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
            theta="Weight",
            color="Criteria",
            tooltip=["Criteria", "Weight"]
        )
        st.altair_chart(chart, use_container_width=True)

    # ---------- PDF ----------
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.add_font("DejaVu", "B", "DejaVuSans.ttf", uni=True)

    pdf.set_font("DejaVu", "B", 16)
    pdf.cell(0, 10, "HR Prompt Engineering Tool Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 8, f"JOB DESCRIPTION:\n{jd}")
    pdf.ln(5)

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, "Technical Questions:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for q in tech_qs:
        pdf.multi_cell(0, 8, f"- {q}")

    pdf.ln(3)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, "Behavioral Questions:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for q in behav_qs:
        pdf.multi_cell(0, 8, f"- {q}")

    pdf.ln(3)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, "Assessment Tasks:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for t in tasks:
        pdf.multi_cell(0, 8, f"- {t}")

    pdf.ln(3)
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 8, "Scoring Rubric:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for k, v in rubric.items():
        pdf.cell(0, 8, f"{k}: {v}%", ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")

    st.download_button(
        "Download PDF Report",
        data=pdf_bytes,
        file_name="hr_report.pdf",
        mime="application/pdf"
    )

    st.success("PDF generated successfully")
