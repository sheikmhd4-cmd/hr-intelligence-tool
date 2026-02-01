import streamlit as st
import pandas as pd
from supabase import create_client
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, ListFlowable, ListItem
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- 1. CONFIGURATION ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- 2. YOUR OLD CODE LOGIC (Restored) ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "ML", "data analysis": "Data",
    "devops": "DevOps", "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

ROLE_MAP = {
    "ml": "Machine Learning Engineer", "data": "Data Analyst",
    "devops": "DevOps Engineer", "backend": "Backend Developer",
    "frontend": "Frontend Developer", "cloud": "Cloud Engineer",
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
        if level == "Junior": qs.append(f"What is {s}? Where have you used it?")
        elif level == "Mid": qs.append(f"Explain a project where you applied {s}. What challenges arose?")
        else: qs.append(f"Design a production-grade system using {s}. How would you scale it?")
    return qs

# ---------------- 3. SESSION STATE ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"

# ---------------- 4. LOGIN / SIGNUP UI ----------------
if not st.session_state.auth_status:
    st.title("💼 HR Intelligence Portal")
    choice = st.radio("Select Action", ["Login", "Sign Up"])
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if choice == "Login":
        role_select = st.selectbox("Login as", ["user", "admin"])
        if st.button("Sign In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.auth_status = True
                st.session_state.user_role = role_select
                st.rerun()
            except:
                st.error("Login Failed. Check Supabase Auth Users.")
    else:
        if st.button("Register Account"):
            supabase.auth.sign_up({"email": email, "password": password})
            st.success("Registration Sent! Check your email or try logging in.")

# ---------------- 5. MAIN APP (Protected) ----------------
else:
    st.sidebar.title(f"Role: {st.session_state.user_role.upper()}")
    page = st.sidebar.radio("Navigate", ["Generator", "History"])
    
    if st.sidebar.button("Logout"):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Generator":
        st.title("🧠 HR Intelligence Tool")
        
        # --- INPUTS (Your Old Code Structure) ---
        uploaded_file = st.file_uploader("Upload JD (.txt)", type=["txt"])
        if uploaded_file:
            jd = uploaded_file.read().decode("utf-8")
        else:
            jd = st.text_area("Paste Job Description", height=220)

        # --- SCORING RUBRIC ---
        st.subheader("🎯 Scoring Rubric")
        c1, c2, c3, c4 = st.columns(4)
        with c1: tech_w = st.slider("Technical", 0, 100, 40)
        with c2: ps_w = st.slider("Problem Solving", 0, 100, 25)
        with c3: sd_w = st.slider("System Design", 0, 100, 20)
        with c4: comm_w = st.slider("Communication", 0, 100, 15)

        difficulty = st.selectbox("Candidate Level", ["Junior", "Mid", "Senior"])
        cand_name = st.text_input("Candidate Name")

        if st.button("🚀 Generate Interview Framework") and jd:
            skills = extract_skills(jd)
            role = guess_role(skills)
            questions = generate_questions(skills, difficulty)
            
            # --- SAVE TO SUPABASE ---
            total = tech_w + ps_w + sd_w + comm_w
            history_data = {
                "candidate_name": cand_name if cand_name else "Unknown",
                "jd_role": role,
                "total_score": float(total),
                "created_by": st.session_state.user_role
            }
            supabase.table("candidate_results").insert(history_data).execute()
            
            st.success("Framework Generated & Saved to Cloud!")

            # --- PDF BUILDER (Restored your specific style) ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            story = [
                Paragraph("<b>HR Intelligence Interview Report</b>", styles["Title"]),
                Spacer(1, 20),
                Paragraph(f"<b>Candidate:</b> {cand_name}", styles["Normal"]),
                Paragraph(f"<b>Detected Role:</b> {role}", styles["Normal"]),
                Spacer(1, 15),
                Paragraph("<b>Technical Questions</b>", styles["Heading2"]),
                ListFlowable([ListItem(Paragraph(q, styles["Normal"])) for q in questions])
            ]
            doc.build(story)

            st.download_button(
                "📥 Download PDF Report",
                data=buffer.getvalue(),
                file_name="HR_Report.pdf",
                mime="application/pdf"
            )

    elif page == "History":
        st.title("📊 History Logs")
        res = supabase.table("candidate_results").select("*").execute()
        df = pd.DataFrame(res.data)

        if not df.empty:
            if st.session_state.user_role == "admin":
                st.subheader("Admin Master History")
                st.dataframe(df)
                if st.button("🗑️ Clear All History"):
                    supabase.table("candidate_results").delete().neq("id", 0).execute()
                    st.rerun()
            else:
                st.subheader("Recent Candidate Logs")
                st.table(df[["candidate_name", "jd_role", "total_score"]].tail(10))