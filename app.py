import streamlit as st
import pandas as pd
import pickle
import os
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import json

# ---------------- FILE BASED PERSISTENT STORAGE ----------------
USERS_FILE = "skillsense_users.pkl"
HISTORY_FILE = "skillsense_history.pkl"

# Load/Save functions
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'rb') as f:
            return pickle.load(f)
    return {
        "user@gmail.com": {"password": "user123", "role": "user"},
        "hr@company.com": {"password": "hr456", "role": "user"}
    }

def save_users(users):
    with open(USERS_FILE, 'wb') as f:
        pickle.dump(users, f)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'rb') as f:
            return pickle.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'wb') as f:
        pickle.dump(history, f)

# Load data
users_db = load_users()
history_db = load_history()

ADMIN_AUTH_CODE = "SSAI-ADMIN-2026-X7K9"

SKILL_SENSE_DB = {
    "python": "Python", "java": "Java", "react": "React", "sql": "SQL", 
    "aws": "AWS", "docker": "Docker", "angular": "Angular", "node": "Node.js",
    "javascript": "JavaScript", "mysql": "MySQL", "git": "Git"
}

def extract_resume_skills(resume_text):
    if not resume_text: return []
    text = resume_text.lower()
    found_skills = []
    for keyword, skill in SKILL_SENSE_DB.items():
        if keyword in text:
            found_skills.append(skill)
    return list(set(found_skills))[:8]

def generate_hiring_recommendation(skills, level):
    skill_count = len(skills)
    score = min(95, 25 + skill_count * 8)
    if skill_count >= (3 if level == "Junior" else 6 if level == "Mid" else 8):
        return "HIRE - Strong candidate", "Strong Match", score
    return "NO HIRE - Needs more skills", "Skill Gap", score

def generate_interview_questions(skills, level):
    questions = []
    for skill in skills[:5]:
        questions.extend([
            f"Can you describe your hands-on experience with {skill}?",
            f"What was the most challenging project you worked on using {skill}?"
        ])
    return questions[:8]

def generate_hiring_pdf(results):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []
    
    # HEADER
    story.append(Paragraph("SkillSense AI - Resume Analysis Report", styles['Title']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # CANDIDATE INFO TABLE
    candidate_data = [["Candidate Name:", results['candidate']], 
                     ["Position Level:", results['level']],
                     ["Analysis Date:", datetime.now().strftime('%Y-%m-%d')]]
    
    candidate_table = Table(candidate_data, colWidths=[2*inch, 3.5*inch])
    candidate_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 12)
    ]))
    story.extend([candidate_table, Spacer(1, 20)])
    
    # MAIN DECISION TABLE
    decision_data = [
        ["Metric", "Status", "Score"],
        ["Hiring Decision", results['hire_decision'], f"{results['score']}%"],
        ["Skill Match", results['status'], f"{len(results['skills'])} Skills"],
        ["Recommendation", "IMMEDIATE ACTION", "PRIORITY"]
    ]
    
    decision_table = Table(decision_data, colWidths=[1.8*inch, 2.2*inch, 1.8*inch])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen if "HIRE" in results['hire_decision'] else colors.lightcoral),
        ('GRID', (0, 0), (-1, -1), 2, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('FONTNAME', (1, 2), (1, 2), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 2), (1, 2), colors.darkred)
    ]))
    
    story.extend([Paragraph("HIRING DECISION SUMMARY", styles['Heading1']), 
                 Spacer(1, 12), decision_table, Spacer(1, 20)])
    
    # SKILLS GRID
    story.append(Paragraph("DETECTED TECHNICAL SKILLS", styles['Heading2']))
    if results['skills']:
        skills_data = []
        for i in range(0, len(results['skills']), 2):
            row = [results['skills'][i]]
            if i+1 < len(results['skills']):
                row.append(results['skills'][i+1])
            skills_data.append(row)
        
        skills_table = Table(skills_data, colWidths=[3*inch, 3*inch], repeatRows=1)
        skills_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.ivory),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.darkgreen),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]))
        story.append(skills_table)
    story.append(Spacer(1, 20))
    
    # ANALYSIS
    story.append(Paragraph("DETAILED ANALYSIS", styles['Heading2']))
    analysis_para = Paragraph(f"""
    <b>Score Breakdown:</b> {results['score']}% match based on {len(results['skills'])} detected skills<br/>
    <b>Threshold Met:</b> {'YES' if results['score'] >= 70 else 'NO'}<br/>
    <b>Position Fit:</b> {results['level']} level - {results['status']}<br/><br/>
    <b>Recommendation:</b> {results['hire_decision']}
    """, styles['Normal'])
    story.append(analysis_para)
    
    # INTERVIEW QUESTIONS (Admin only)
    if st.session_state.get('user_role') == "admin" and 'questions' in results:
        story.append(Spacer(1, 20))
        story.append(Paragraph("INTERVIEW QUESTIONS", styles['Heading2']))
        for i, question in enumerate(results['questions'][:6], 1):
            story.append(Paragraph(f"{i}. {question}", styles['Normal']))
            story.append(Spacer(1, 8))
    
    # FOOTER
    story.append(Spacer(1, 20))
    footer_data = [["Generated by:", "SkillSense AI Enterprise"], 
                  ["Report ID:", f"SSAI-{datetime.now().strftime('%Y%m%d%H%M')}"]]
    footer_table = Table(footer_data, colWidths=[2*inch, 3.5*inch])
    footer_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(footer_table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------- SESSION STATE ----------------
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'current_user' not in st.session_state: 
    st.session_state.current_user = None
if 'user_role' not in st.session_state: 
    st.session_state.user_role = None
if 'results' not in st.session_state: 
    st.session_state.results = None

st.set_page_config(page_title="SkillSense AI", layout="wide")

# ---------------- MAIN APP ----------------
if not st.session_state.logged_in:
    st.title("SkillSense AI")
    st.markdown("### Professional Resume Analysis Platform")
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])  # NO ADMIN TAB
    
    # TAB 1: LOGIN
    with tab1:
        st.markdown("**Login with your saved account**")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("LOGIN", type="primary"):
                if email in users_db and users_db[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.session_state.user_role = users_db[email]["role"]
                    st.success(f"Welcome back {email}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
                    st.info("**Default:** user@gmail.com / user123")
    
    # TAB 2: CREATE ACCOUNT
    with tab2:
        st.markdown("**Create New Account (Saved Forever)**")
        with st.form("create_account"):
            email = st.text_input("New Email")
            password = st.text_input("New Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Create USER Account", type="secondary"):
                    if email and password:
                        if email not in users_db:
                            users_db[email] = {"password": password, "role": "user"}
                            save_users(users_db)
                            st.success(f"✅ User account SAVED: {email}")
                            st.info("Login anytime with same details!")
                        else:
                            st.error("Email already exists!")
                    else:
                        st.error("Fill all fields!")
            
            with col2:
                admin_code = st.text_input("Admin Auth Code", type="password", 
                                         placeholder="")
                if st.form_submit_button("Create ADMIN Account", type="primary"):
                    if email and password:
                        if email not in users_db:
                            if admin_code == ADMIN_AUTH_CODE:
                                users_db[email] = {"password": password, "role": "admin"}
                                save_users(users_db)
                                st.success(f"✅ Admin account SAVED: {email}")
                            else:
                                st.error("❌ Wrong admin code!")
                        else:
                            st.error("Email already exists!")
                    else:
                        st.error("Fill all fields!")

else:
    # DASHBOARD
    st.sidebar.markdown("**SkillSense AI**")
    st.sidebar.markdown(f"**User:** {st.session_state.current_user}")
    st.sidebar.markdown(f"**Role:** {st.session_state.user_role.upper()}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_role = None
        st.session_state.results = None
        st.rerun()
    
    # Navigation
    if st.session_state.user_role == "admin":
        page = st.sidebar.radio("Dashboard", ["Resume Analyzer", "History", "Admin"])
    else:
        page = st.sidebar.radio("Dashboard", ["Resume Analyzer"])
    
    if page == "Resume Analyzer":
        st.title("Resume Analyzer")
        
        col1, col2 = st.columns([2,1])
        with col1:
            resume_text = st.text_area("Paste Resume", height=300)
        with col2:
            name = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            
            if st.button("ANALYZE RESUME", type="primary"):
                skills = extract_resume_skills(resume_text)
                decision, status, score = generate_hiring_recommendation(skills, level)
                
                result = {
                    "candidate": name or "Candidate",
                    "skills": skills,
                    "level": level,
                    "hire_decision": decision,
                    "status": status,
                    "score": score,
                    "questions": generate_interview_questions(skills, level),
                    "timestamp": datetime.now().isoformat()
                }
                
                st.session_state.results = result
                history_db.append(result)
                save_history(history_db)
                st.success("Analysis saved!")
        
        if st.session_state.results:
            r = st.session_state.results
            
            if "HIRE" in r['hire_decision']:
                st.markdown(f"""
                <div style='background:linear-gradient(45deg,#4CAF50,#45a049);
                padding:30px;border-radius:15px;color:white;text-align:center'>
                <h1>HIRE RECOMMENDED</h1><h2>{r['score']}%</h2></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:linear-gradient(45deg,#f44336,#d32f2f);
                padding:30px;border-radius:15px;color:white;text-align:center'>
                <h1>NO HIRE</h1><h2>{r['score']}%</h2></div>""", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Skills", len(r["skills"]))
            with col2: st.metric("Level", r["level"])
            with col3: st.metric("Score", f"{r['score']}%")
            
            st.subheader("Skills Found")
            for skill in r["skills"]:
                st.success(skill)
            
            if st.session_state.user_role == "admin":
                st.subheader("Interview Questions")
                for i, q in enumerate(r["questions"][:5], 1):
                    st.info(f"Q{i}: {q}")
                
                pdf_data = generate_hiring_pdf(r)
                st.download_button(
                    "Download PDF Report",
                    pdf_data.getvalue(),
                    f"SkillSense_{r['candidate'].replace(' ', '_')}.pdf",
                    "application/pdf"
                )
    
    elif page == "History" and st.session_state.user_role == "admin":
        st.title("Analysis History")
        if history_db:
            df = pd.DataFrame(history_db)
            st.dataframe(df[['candidate', 'hire_decision', 'score', 'timestamp']], use_container_width=True)
        else:
            st.info("No analysis history yet")
    
    elif page == "Admin" and st.session_state.user_role == "admin":
        st.title("Admin Panel")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("All User Accounts")
            user_df = pd.DataFrame([
                {"Email": email, "Role": info["role"]} 
                for email, info in users_db.items()
            ])
            st.dataframe(user_df)
            st.info(f"**Files:** skillsense_users.pkl, skillsense_history.pkl")
        
        with col2:
            if st.button("Delete All Data"):
                if os.path.exists(USERS_FILE):
                    os.remove(USERS_FILE)
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                st.success("All data deleted!")
                st.rerun()

st.markdown("---")
st.markdown("**SkillSense AI © 2026 | Professional Resume Analysis**")
