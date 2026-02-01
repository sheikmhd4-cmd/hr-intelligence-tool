import streamlit as st
import pandas as pd
from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# ---------------- 1. CONFIGURATION & CLIENT ----------------
# Using the keys from your .env file
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- 2. ORIGINAL LOGIC (Unchanged) ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "react": "React"
}

ROLE_MAP = {
    "ml": "Machine Learning Engineer", 
    "data": "Data Analyst", 
    "devops": "DevOps Engineer"
}

def extract_skills(text):
    found = []
    t = text.lower()
    for k, v in SKILL_DB.items():
        if k in t: found.append(v)
    return list(set(found))

def guess_role(skills):
    s = " ".join(skills).lower()
    for k, v in ROLE_MAP.items():
        if k in s: return v
    return "Software Engineer"

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior":
            qs.append(f"Basic: What are the core concepts of {s}?")
        elif level == "Mid":
            qs.append(f"Intermediate: Describe a complex scenario where you used {s}.")
        else:
            qs.append(f"Advanced: How would you architect a system using {s} for high availability?")
    return qs

# ---------------- 3. SESSION MANAGEMENT ----------------
if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

# ---------------- 4. AUTHENTICATION UI ----------------
def show_auth_page():
    st.title("🔐 HR Intelligence Portal")
    mode = st.tabs(["Login", "Register"])
    
    with mode[0]:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        role = st.selectbox("Login as", ["user", "admin"])
        if st.button("Sign In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.is_authenticated = True
                st.session_state.user_role = role
                st.rerun()
            except Exception:
                st.error("Authentication Failed. Check credentials or Supabase Auth settings.")

    with mode[1]:
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            supabase.auth.sign_up({"email": new_email, "password": new_pass})
            st.success("Registration successful! You can now log in.")

# ---------------- 5. MAIN PROTECTED APP ----------------
if not st.session_state.is_authenticated:
    show_auth_page()
else:
    # Sidebar Navigation
    st.sidebar.title(f"Role: {st.session_state.user_role.upper()}")
    app_mode = st.sidebar.radio("Navigation", ["Framework Generator", "Candidate History"])
    
    if st.sidebar.button("Log Out"):
        st.session_state.is_authenticated = False
        st.rerun()

    if app_mode == "Framework Generator":
        st.title("🧠 Interview Framework Generator")
        
        # User Inputs
        candidate = st.text_input("Candidate Name")
        jd_input = st.text_area("Paste Job Description", height=200)
        level = st.selectbox("Experience Level", ["Junior", "Mid", "Senior"])
        
        # Scoring Rubric (Old Sliders)
        st.subheader("🎯 Scoring Rubric")
        c1, c2, c3, c4 = st.columns(4)
        with c1: tech = st.slider("Technical", 0, 100, 40)
        with c2: prob = st.slider("Problem Solving", 0, 100, 25)
        with c3: sys_d = st.slider("System Design", 0, 100, 20)
        with c4: comm = st.slider("Communication", 0, 100, 15)

        if st.button("🚀 Generate & Sync to Cloud"):
            if jd_input:
                # Run Logic
                found_skills = extract_skills(jd_input)
                detected_role = guess_role(found_skills)
                questions = generate_questions(found_skills, level)
                total = tech + prob + sys_d + comm

                # --- SUPABASE DATABASE SYNC ---
                history_entry = {
                    "candidate_name": candidate if candidate else "Anonymous",
                    "jd_role": detected_role,
                    "score": total,
                    "created_by": st.session_state.user_role
                }
                supabase.table("candidate_results").insert(history_entry).execute()
                
                st.success("Framework Generated and Saved to Supabase!")

                # --- PDF GENERATOR ---
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                elements = [
                    Paragraph(f"Interview Report - {detected_role}", styles['Title']),
                    Spacer(1, 12),
                    Paragraph(f"Candidate: {candidate}", styles['Normal']),
                    Paragraph(f"Skills: {', '.join(found_skills)}", styles['Normal']),
                    Spacer(1, 12),
                    Paragraph("Questions:", styles['Heading2'])
                ]
                for q in questions:
                    elements.append(Paragraph(f"• {q}", styles['Normal']))

                doc.build(elements)
                
                st.download_button(
                    label="📥 Download PDF Report",
                    data=buffer.getvalue(),
                    file_name=f"{candidate}_interview.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Please provide a Job Description.")

    elif app_mode == "Candidate History":
        st.title("📊 History Logs")
        
        # Fetch Data
        response = supabase.table("candidate_results").select("*").execute()
        data_df = pd.DataFrame(response.data)

        if not data_df.empty:
            if st.session_state.user_role == "admin":
                st.info("Admin Access: View and Manage all records.")
                st.dataframe(data_df)
                if st.button("🗑️ Clear Entire History"):
                    supabase.table("candidate_results").delete().neq("id", 0).execute()
                    st.rerun()
            else:
                st.info("User Access: View recent entries.")
                st.table(data_df[["candidate_name", "jd_role", "score"]].tail(10))
        else:
            st.write("No history records found.")