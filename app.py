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
from sentence_transformers import SentenceTransformer, util
import numpy as np

# FILE BASED PERSISTENT STORAGE
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

def generate_interview_questions(detected_skills, level):
    """Generate targeted interview questions based on detected skills"""
    questions = []
    for skill in detected_skills[:5]:
        questions.extend([
            f"Can you describe your hands-on experience with {skill}?",
            f"What was the most challenging project you worked on using {skill}?",
            f"How do you approach debugging issues in {skill} projects?"
        ])
    return questions[:8]

# AI FUNCTION (HUGGINGFACE)
@st.cache_resource
def load_ai_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def ai_resume_analysis(resume_text, job_role="Software Developer"):
    try:
        model = load_ai_model()
        
        # Extract skills from resume
        resume_lower = resume_text.lower()
        detected_skills = []
        skill_list = ["python", "react", "java", "sql", "aws", "docker", "angular", "node", "javascript", "mysql"]
        
        for skill in skill_list:
            if skill in resume_lower:
                detected_skills.append(skill.title())
        
        # Job required skills
        job_skills = ["python", "react", "sql", "aws", "docker", "node"]
        
        # AI Similarity calculation
        if detected_skills:
            resume_text = ", ".join(detected_skills)
            job_text = ", ".join(job_skills)
            resume_emb = model.encode([resume_text])
            job_emb = model.encode([job_text])
            similarity = util.cos_sim(resume_emb, job_emb).item() * 100
        else:
            similarity = 20
        
        # AI Recommendation
        score = min(95, max(25, int(similarity)))
        recommendation = "HIRE" if score > 75 else "INTERVIEW" if score > 50 else "REVIEW"
        
        # Generate interview questions
        interview_questions = generate_interview_questions(detected_skills, "Mid")
        
        return {
            "ai_score": score,
            "recommendation": recommendation,
            "detected_skills": detected_skills[:8],
            "job_fit": f"{score}% match for {job_role}",
            "strengths": detected_skills[:3],
            "confidence": "High" if score > 70 else "Medium",
            "interview_questions": interview_questions
        }
    except:
        return {
            "ai_score": 50,
            "recommendation": "REVIEW",
            "detected_skills": [],
            "job_fit": "AI temporarily unavailable",
            "strengths": [],
            "confidence": "Low",
            "interview_questions": []
        }

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
                     ["Position Level:", results.get('level', 'N/A')],
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
    ai_score = results.get('ai_score', 0)
    decision_data = [
        ["Metric", "Status", "Score"],
        ["Hiring Decision", results.get('recommendation', 'N/A'), f"{ai_score}%"],
        ["Skill Match", f"{len(results.get('detected_skills', []))} Skills"],
        ["AI Recommendation", results.get('job_fit', 'N/A')]
    ]
    
    decision_table = Table(decision_data, colWidths=[1.8*inch, 2.2*inch, 1.8*inch])
    decision_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen if ai_score > 70 else colors.lightcoral),
        ('GRID', (0, 0), (-1, -1), 2, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 12)
    ]))
    
    story.extend([Paragraph("AI-ENHANCED HIRING DECISION", styles['Heading1']), 
                 Spacer(1, 12), decision_table, Spacer(1, 20)])
    
    # SKILLS GRID
    all_skills = results.get('detected_skills', [])
    story.append(Paragraph("DETECTED TECHNICAL SKILLS", styles['Heading2']))
    if all_skills:
        skills_data = []
        for i in range(0, len(all_skills), 2):
            row = [all_skills[i]]
            if i+1 < len(all_skills):
                row.append(all_skills[i+1])
            skills_data.append(row)
        
        skills_table = Table(skills_data, colWidths=[3*inch, 3*inch])
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
    
    # INTERVIEW QUESTIONS
    questions = results.get('interview_questions', [])
    if questions:
        story.append(Paragraph("INTERVIEW QUESTIONS", styles['Heading2']))
        for i, question in enumerate(questions[:6], 1):
            story.append(Paragraph(f"{i}. {question}", styles['Normal']))
            story.append(Spacer(1, 8))
    
    # ANALYSIS
    story.append(Paragraph("DETAILED AI ANALYSIS", styles['Heading2']))
    analysis_para = Paragraph(f"""
    <b>AI Score:</b> {ai_score}% semantic match using HuggingFace Transformers<br/>
    <b>Skills Found:</b> {len(all_skills)} technical skills detected<br/>
    <b>Position Fit:</b> {results.get('level', 'N/A')} level position<br/>
    <b>Recommendation:</b> {results.get('recommendation', 'N/A')}<br/><br/>
    
    <b>Powered by:</b> SkillSense AI + HuggingFace AI
    """, styles['Normal'])
    story.append(analysis_para)
    
    # FOOTER
    story.append(Spacer(1, 20))
    footer_data = [["Generated by:", "SkillSense AI Enterprise + HuggingFace AI"], 
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

# SESSION STATE
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False
if 'current_user' not in st.session_state: 
    st.session_state.current_user = None
if 'user_role' not in st.session_state: 
    st.session_state.user_role = None
if 'results' not in st.session_state: 
    st.session_state.results = None

st.set_page_config(page_title="SkillSense AI", layout="wide")

# MAIN APP
if not st.session_state.logged_in:
    st.title("SkillSense AI")
    st.markdown("Professional Resume Analysis Platform")
    
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    # TAB 1: LOGIN
    with tab1:
        st.markdown("Login with your saved account")
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
                    st.info("Default: user@gmail.com / user123")
    
    # TAB 2: CREATE ACCOUNT
    with tab2:
        st.markdown("Create New Account")
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
                            st.success(f"User account SAVED: {email}")
                            st.info("Login anytime with same details!")
                        else:
                            st.error("Email already exists!")
                    else:
                        st.error("Fill all fields!")
            
            with col2:
                admin_code = st.text_input("Admin Auth Code", type="password", placeholder="Enter your Passkey")
                if st.form_submit_button("Create ADMIN Account", type="primary"):
                    if email and password:
                        if email not in users_db:
                            if admin_code == ADMIN_AUTH_CODE:
                                users_db[email] = {"password": password, "role": "admin"}
                                save_users(users_db)
                                st.success(f"Admin account SAVED: {email}")
                            else:
                                st.error("Wrong admin code!")
                        else:
                            st.error("Email already exists!")
                    else:
                        st.error("Fill all fields!")

else:
    # DASHBOARD
    st.sidebar.markdown("SkillSense AI")
    st.sidebar.markdown(f"User: {st.session_state.current_user}")
    st.sidebar.markdown(f"Role: {st.session_state.user_role.upper()}")
    
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
        st.title("SkillSense AI - Resume Analyzer")
        
        col1, col2 = st.columns([2,1])
        with col1:
            resume_text = st.text_area("Paste Resume", height=300)
        with col2:
            name = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
        
        # AI ANALYSIS BUTTON
        if st.button("AI ANALYSIS", type="primary", use_container_width=True):
            with st.spinner("AI analyzing with HuggingFace Transformers..."):
                ai_result = ai_resume_analysis(resume_text)
                ai_result["candidate"] = name or "Candidate"
                ai_result["level"] = level
                st.session_state.results = ai_result
                history_db.append(ai_result)
                save_history(history_db)
                st.success(f"AI Score: {ai_result['ai_score']}%")
        
        # DISPLAY RESULTS
        if st.session_state.get('results'):
            r = st.session_state.results
            ai_score = r.get('ai_score', 0)
            
            if ai_score > 75:
                st.markdown(f"""
                <div style='background:linear-gradient(45deg,#4CAF50,#45a049);
                padding:30px;border-radius:15px;color:white;text-align:center'>
                <h1>HIRE RECOMMENDED</h1><h2>{ai_score}%</h2></div>""", unsafe_allow_html=True)
            elif ai_score > 50:
                st.markdown(f"""
                <div style='background:linear-gradient(45deg,#FF9800,#F57C00);
                padding:30px;border-radius:15px;color:white;text-align:center'>
                <h1>INTERVIEW</h1><h2>{ai_score}%</h2></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:linear-gradient(45deg,#f44336,#d32f2f);
                padding:30px;border-radius:15px;color:white;text-align:center'>
                <h1>REVIEW NEEDED</h1><h2>{ai_score}%</h2></div>""", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Skills Found", len(r.get("detected_skills", [])))
            with col2: st.metric("Target Level", r.get("level", "N/A"))
            with col3: st.metric("AI Score", f"{ai_score}%")
            
            st.subheader("AI Detected Skills")
            for skill in r.get("detected_skills", []):
                st.success(skill)
            
            # INTERVIEW QUESTIONS
            questions = r.get("interview_questions", [])
            if questions:
                st.subheader("Interview Questions")
                for i, q in enumerate(questions[:6], 1):
                    st.info(f"Q{i}: {q}")
            
            st.caption("Powered by HuggingFace Sentence Transformers")
        
        # PDF DOWNLOAD (Admin only)
        if st.session_state.results and st.session_state.user_role == "admin":
            pdf_data = generate_hiring_pdf(st.session_state.results)
            st.download_button(
                "Download AI-Enhanced PDF Report",
                pdf_data.getvalue(),
                f"SkillSense_AI_Report_{st.session_state.results['candidate'].replace(' ', '_')}.pdf",
                "application/pdf"
            )
    
    elif page == "History" and st.session_state.user_role == "admin":
        st.title("Analysis History")
        if history_db:
            df = pd.DataFrame(history_db)
            st.dataframe(df[['candidate', 'recommendation', 'ai_score', 'timestamp']], use_container_width=True)
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
            st.info(f"Files: skillsense_users.pkl, skillsense_history.pkl")
        
        with col2:
            if st.button("Delete All Data"):
                if os.path.exists(USERS_FILE):
                    os.remove(USERS_FILE)
                if os.path.exists(HISTORY_FILE):
                    os.remove(HISTORY_FILE)
                st.success("All data deleted!")
                st.rerun()

st.markdown("---")
st.markdown("SkillSense AI 2026 | Powered by HuggingFace Transformers")
