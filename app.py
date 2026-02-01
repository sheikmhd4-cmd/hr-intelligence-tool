import streamlit as st
import pandas as pd
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="HR Intelligence Tool",
    layout="wide",
    page_icon="💼"
)

# ---------------- TITLE ----------------
st.title("🧠 HR Intelligence Tool")
st.markdown("### Convert Job Descriptions into Smart Interview Frameworks")

# ---------------- INPUT ----------------
uploaded_file = st.file_uploader("Upload JD (.txt)", type=["txt"])

if uploaded_file:
    jd = uploaded_file.read().decode("utf-8")
else:
    jd = st.text_area("Paste Job Description", height=220)

# ---------------- JD ANALYSIS ----------------

SKILL_DB = {
    "python": "Python",
    "sql": "SQL",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "react": "React",
    "machine learning": "ML",
    "data analysis": "Data",
    "devops": "DevOps",
    "ci/cd": "CI/CD",
    "terraform": "Terraform",
    "linux": "Linux",
}

ROLE_MAP = {
    "ml": "Machine Learning Engineer",
    "data": "Data Analyst",
    "devops": "DevOps Engineer",
    "backend": "Backend Developer",
    "frontend": "Frontend Developer",
    "cloud": "Cloud Engineer",
}

def extract_skills(text):
    found = []
    t = text.lower()
    for k, v in SKILL_DB.items():
        if k in t:
            found.append(v)
    return list(set(found))

def guess_role(skills):
    s = " ".join(skills).lower()
    for k, v in ROLE_MAP.items():
        if k in s:
            return v
    return "Software Engineer"

skills = extract_skills(jd) if jd else []
role = guess_role(skills)

# ---------------- RUBRIC ----------------

st.subheader("🎯 Scoring Rubric")

col1, col2, col3, col4 = st.columns(4)

with col1:
    tech_w = st.slider("Technical", 0, 100, 40)
with col2:
    ps_w = st.slider("Problem Solving", 0, 100, 25)
with col3:
    sd_w = st.slider("System Design", 0, 100, 20)
with col4:
    comm_w = st.slider("Communication", 0, 100, 15)

rubric = {
    "Technical": tech_w,
    "Problem Solving": ps_w,
    "System Design": sd_w,
    "Communication": comm_w,
}

# ---------------- QUESTION ENGINE ----------------

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior":
            qs.append(f"What is {s}? Where have you used it?")
        elif level == "Mid":
            qs.append(f"Explain a project where you applied {s}. What challenges arose?")
        else:
            qs.append(f"Design a production-grade system using {s}. How would you scale it?")
    return qs

difficulty = st.selectbox("Candidate Level", ["Junior", "Mid", "Senior"])

# ---------------- GENERATE ----------------

if st.button("🚀 Generate Interview Framework") and jd:

    st.success("Framework generated successfully!")

    questions = generate_questions(skills, difficulty)

    st.subheader("📌 Detected Role")
    st.write(role)

    st.subheader("🛠 Skills Found")
    st.write(", ".join(skills) if skills else "General Software Skills")

    st.subheader("💬 Technical Questions")
    for q in questions:
        st.write("•", q)

    st.subheader("🤝 Behavioral Questions")
    behav = [
        "Describe a difficult technical decision you made.",
        "How do you handle pressure?",
        "Explain a conflict in your team and resolution.",
        "How do you keep skills updated?",
    ]
    for b in behav:
        st.write("•", b)

    # ---------------- PDF BUILD ----------------

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b>HR Intelligence Interview Report</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    story.append(Paragraph(f"<b>Detected Role:</b> {role}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Job Description</b>", styles["Heading2"]))
    story.append(Paragraph(jd, styles["Normal"]))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Skills Detected</b>", styles["Heading2"]))
    story.append(Paragraph(", ".join(skills), styles["Normal"]))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Technical Questions</b>", styles["Heading2"]))

    story.append(ListFlowable(
        [ListItem(Paragraph(q, styles["Normal"])) for q in questions]
    ))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Behavioral Questions</b>", styles["Heading2"]))

    story.append(ListFlowable(
        [ListItem(Paragraph(b, styles["Normal"])) for b in behav]
    ))

    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Scoring Rubric</b>", styles["Heading2"]))

    rubric_table = Table([[k, f"{v}%"] for k, v in rubric.items()])
    rubric_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 1, colors.grey)
    ]))

    story.append(rubric_table)

    pdf_path = "hr_interview_report.pdf"

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    doc.build(story)

    with open(pdf_path, "rb") as f:
        st.download_button(
            "📥 Download Professional PDF",
            f,
            file_name="HR_Interview_Report.pdf",
            mime="application/pdf"
        )
