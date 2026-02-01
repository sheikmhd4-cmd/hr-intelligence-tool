import streamlit as st
import pandas as pd
from supabase import create_client
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

# --- 1. SUPABASE CONNECTION ---
# Intha keys unga .env la irunthu varuthu
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. OLD CODE FUNCTIONS (Logic-ah maathala) ---
SKILL_DB = {"python": "Python", "sql": "SQL", "docker": "Docker", "kubernetes": "Kubernetes", "aws": "AWS", "react": "React"}
ROLE_MAP = {"ml": "Machine Learning Engineer", "data": "Data Analyst", "devops": "DevOps Engineer"}

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
        if level == "Junior": qs.append(f"What is {s}? Where have you used it?")
        elif level == "Mid": qs.append(f"Explain a project where you applied {s}.")
        else: qs.append(f"Design a production-grade system using {s}.")
    return qs

# --- 3. SESSION STATE FOR LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

# --- 4. LOGIN PAGE ---
def login_page():
    st.title("🔐 HR Portal Login")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role_choice = st.selectbox("Role", ["user", "admin"])
        if st.button("Login"):
            try:
                # Supabase Auth connection
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.logged_in = True
                st.session_state.user_role = role_choice
                st.rerun()
            except:
                st.error("Invalid Login! Supabase-la user create panniyacha?")

    with tab2:
        new_email = st.text_input("New Email")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Register"):
            supabase.auth.sign_up({"email": new_email, "password": new_pass})
            st.success("Account created! Now login in Tab 1.")

# --- 5. MAIN APPLICATION (After Login) ---
if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.header(f"Welcome {st.session_state.user_role.upper()}")
    menu = ["Generator", "History"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    if choice == "Generator":
        st.title("🧠 HR Intelligence Tool")
        
        # JD Input
        jd = st.text_area("Paste Job Description", height=200)
        
        # Rubric (Old Sliders)
        col1, col2, col3, col4 = st.columns(4)
        with col1: tech_w = st.slider("Technical", 0, 100, 40)
        with col2: ps_w = st.slider("Problem Solving", 0, 100, 25)
        with col3: sd_w = st.slider("System Design", 0, 100, 20)
        with col4: comm_w = st.slider("Communication", 0, 100, 15)
        
        level = st.selectbox("Candidate Level", ["Junior", "Mid", "Senior"])
        candidate_name = st.text_input("Candidate Name")

        if st.button("🚀 Generate & Save History"):
            if jd:
                skills = extract_skills(jd)
                role = guess_role(skills)
                questions = generate_questions(skills, level)
                
                # --- SAVE TO SUPABASE ---
                history_data = {
                    "candidate_name": candidate_name if candidate_name else "Unknown",
                    "role": role,
                    "total_score": float(tech_w + ps_w + sd_w + comm_w),
                    "created_by": st.session_state.user_role
                }
                supabase.table("candidate_results").insert(history_data).execute()
                
                st.success("Framework Generated & Saved!")
                
                # --- PDF GENERATION (Old Logic) ---
                styles = getSampleStyleSheet()
                story = [Paragraph(f"Interview Report: {role}", styles['Title'])]
                # ... (Additional PDF content) ...
                
                pdf_path = "report.pdf"
                doc = SimpleDocTemplate(pdf_path, pagesize=A4)
                doc.build(story)
                
                with open(pdf_path, "rb") as f:
                    st.download_button("📥 Download PDF Report", f, file_name=f"{candidate_name}_Report.pdf")
            else:
                st.warning("Please paste a JD.")

    elif choice == "History":
        st.title("📊 History Logs")
        
        # Supabase Fetch
        res = supabase.table("candidate_results").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if not df.empty:
            if st.session_state.user_role == "admin":
                st.write("### Admin View: All History")
                st.dataframe(df)
                if st.button("🗑️ Clear All History"):
                    supabase.table("candidate_results").delete().neq("id", 0).execute()
                    st.rerun()
            else:
                st.write("### User View: Recent Results")
                st.table(df[["candidate_name", "role", "total_score"]].tail(10))
        else:
            st.info("No history found.")