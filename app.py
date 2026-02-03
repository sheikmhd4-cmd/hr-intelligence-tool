import streamlit as st
import pandas as pd
from supabase import create_client
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import json
from datetime import datetime
import re

# ---------------- SUPABASE CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- PROFESSIONAL ADMIN AUTH CODE ----------------
ADMIN_AUTH_CODE = "SSAI-ADMIN-2026-X7K9"

# ---------------- DEFAULT USERS ----------------
DEFAULT_USERS = {
    "user@gmail.com": {"password": "user123", "role": "user"},
    "hr@company.com": {"password": "hr456", "role": "user"}
}

# Dynamic user storage
if 'custom_users' not in st.session_state:
    st.session_state.custom_users = {}

SKILL_SENSE_DB = {
    "python": "Python", "java": "Java", "react": "React", "sql": "SQL", 
    "aws": "AWS", "docker": "Docker", "angular": "Angular", "node": "Node.js"
}

# ---------------- FUNCTIONS ----------------
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
    return [f"Tell me about your {skill} experience?" for skill in skills[:6]]

def save_assessment(results):
    try:
        data = {
            "candidate": results['candidate'],
            "skills": json.dumps(results['skills']),
            "level": results['level'],
            "hire_decision": results['hire_decision'],
            "score": results['score'],
            "status": results['status'],
            "created_at": datetime.now().isoformat()
        }
        supabase.table("assessments").insert(data).execute()
    except: pass

def generate_hiring_pdf(results):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("SkillSense AI - Analysis Report", styles['Title']),
        Paragraph(f"Candidate: {results['candidate']}", styles['Heading1']),
        Paragraph(f"Decision: {results['hire_decision']}", styles['Heading2'])
    ]
    doc.build(story)
    buffer.seek(0)
    return buffer

def get_all_users():
    return {**DEFAULT_USERS, **st.session_state.custom_users}

# ---------------- SESSION STATE ----------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'results' not in st.session_state: st.session_state.results = None
if 'signup_step' not in st.session_state: st.session_state.signup_step = None
if 'temp_email' not in st.session_state: st.session_state.temp_email = None
if 'temp_password' not in st.session_state: st.session_state.temp_password = None

st.set_page_config(page_title="SkillSense AI", layout="wide")

# ---------------- MAIN APP ----------------
if not st.session_state.logged_in:
    st.title("SkillSense AI")
    st.markdown("Professional Resume Analysis Platform")
    
    tab1, tab2, tab3 = st.tabs(["Login", "Create Account", "Admin Access"])
    
    # ---------------- TAB 1: CLEAN LOGIN - NO CREDENTIALS SHOWN ----------------
    with tab1:
        st.markdown("Standard User Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", type="primary"):
                all_users = get_all_users()
                if email in all_users and all_users[email]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.session_state.user_role = all_users[email]["role"]
                    st.success(f"Welcome {email}!")
                    st.rerun()
                else:
                    st.error("Invalid credentials!")
    
    # ---------------- TAB 2: CREATE USER ACCOUNT ----------------
    with tab2:
        st.markdown("Create New User Account")
        
        if st.session_state.signup_step == "authcode":
            st.info(f"Creating Administrator account for: {st.session_state.temp_email}")
            st.warning("Administrative Authorization Code Required")
            auth_code = st.text_input("Admin Auth Code", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Verify Auth Code", type="primary"):
                    if auth_code == ADMIN_AUTH_CODE:
                        st.session_state.custom_users[st.session_state.temp_email] = {
                            "password": st.session_state.temp_password, "role": "admin"
                        }
                        st.session_state.signup_step = None
                        st.success("Administrator account created successfully!")
                    else:
                        st.error("Invalid authorization code!")
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.signup_step = None
                    st.session_state.temp_email = None
                    st.session_state.temp_password = None
                    st.rerun()
        
        else:
            with st.form("create_user"):
                email = st.text_input("New Email")
                password = st.text_input("New Password", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    user_create = st.form_submit_button("Create USER Account", type="secondary")
                with col2:
                    admin_create = st.form_submit_button("Create ADMIN Account", type="primary")
                
                if user_create or admin_create:
                    if email and password:
                        if email in get_all_users():
                            st.error("Email already exists!")
                        else:
                            st.session_state.temp_email = email
                            st.session_state.temp_password = password
                            
                            if admin_create:
                                st.session_state.signup_step = "authcode"
                                st.info("Administrative authorization required!")
                            else:
                                st.session_state.custom_users[email] = {
                                    "password": password, "role": "user"
                                }
                                st.success("User account created!")
                    else:
                        st.error("Fill all fields!")
    
    # ---------------- TAB 3: ADMIN LOGIN ----------------
    with tab3:
        st.markdown("Administrator Login")
        with st.form("admin_login"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("ADMIN LOGIN", type="primary"):
                all_users = get_all_users()
                if email in all_users and all_users[email]["password"] == password and all_users[email]["role"] == "admin":
                    st.session_state.logged_in = True
                    st.session_state.current_user = email
                    st.session_state.user_role = all_users[email]["role"]
                    st.success(f"Welcome Admin {email}!")
                    st.rerun()
                else:
                    st.error("Invalid admin credentials!")

else:
    # ---------------- DASHBOARD ----------------
    st.sidebar.markdown("SkillSense AI")
    st.sidebar.markdown(f"User: {st.session_state.current_user}")
    st.sidebar.markdown(f"Role: {st.session_state.user_role.upper()}")
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.results = None
        st.rerun()
    
    # Navigation
    if st.session_state.user_role == "admin":
        page = st.sidebar.radio("Navigation", ["Resume Analyzer", "Assessment History", "Admin Panel"])
    else:
        page = st.sidebar.radio("Navigation", ["Resume Analyzer"])
    
    # ---------------- RESUME ANALYZER ----------------
    if page == "Resume Analyzer":
        st.title("SkillSense AI - Resume Analyzer")
        
        col1, col2 = st.columns([2,1])
        with col1:
            resume_text = st.text_area("Paste Resume", height=300)
        with col2:
            name = st.text_input("Candidate Name")
            level = st.select_slider("Level", ["Junior", "Mid", "Senior"])
            
            if st.button("ANALYZE RESUME", type="primary"):
                skills = extract_resume_skills(resume_text)
                decision, status, score = generate_hiring_recommendation(skills, level)
                
                st.session_state.results = {
                    "candidate": name or "Candidate",
                    "skills": skills, "level": level,
                    "hire_decision": decision, "status": status, "score": score,
                    "questions": generate_interview_questions(skills, level)
                }
                
                if st.session_state.user_role == "admin":
                    save_assessment(st.session_state.results)
        
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
                for i, q in enumerate(r["questions"], 1):
                    st.info(f"Q{i}: {q}")
                
                pdf_data = generate_hiring_pdf(r)
                st.download_button("PDF Report", pdf_data.getvalue(), 
                    f"SkillSense_{r['candidate']}.pdf", "application/pdf")
    
    # ---------------- OTHER PAGES ----------------
    elif page == "Assessment History" and st.session_state.user_role == "admin":
        st.title("Assessment History")
        try:
            data = supabase.table("assessments").select("*").order("created_at", desc=True).execute()
            if data.data:
                df = pd.DataFrame(data.data)
                df['skills'] = df['skills'].apply(lambda x: json.loads(x) if x else [])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No data yet")
        except:
            st.info("Table needed")
    
    elif page == "Admin Panel" and st.session_state.user_role == "admin":
        st.title("Admin Panel")
        st.success("Admin Access Granted!")
        
        st.subheader("Created Accounts")
        all_users = get_all_users()
        user_df = pd.DataFrame([
            {"Email": email, "Role": info["role"]} 
            for email, info in all_users.items()
        ])
        st.dataframe(user_df)

st.markdown("---")
st.markdown("SkillSense AI © 2026 | Enterprise Authentication System", unsafe_allow_html=True)
