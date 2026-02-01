import streamlit as st
import pandas as pd
from supabase import create_client
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Page Config for Professional Look
st.set_page_config(page_title="HR Intel Portal", layout="wide")

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "ML", "data analysis": "Data",
    "devops": "DevOps", "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

def extract_skills(text):
    found = []
    t = text.lower()
    for k, v in SKILL_DB.items():
        if k in t: found.append(v)
    return list(set(found))

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior": qs.append(f"Foundational concepts of {s} and practical usage.")
        elif level == "Mid": qs.append(f"Implementation strategies and troubleshooting {s}.")
        else: qs.append(f"Architectural decision-making and optimization using {s}.")
    return qs

# ---------------- AUTH UI ----------------
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False

if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("HR Intelligence Portal")
        st.markdown("---")
        choice = st.tabs(["Secure Login", "Account Registration"])
        
        with choice[0]:
            email = st.text_input("Corporate Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            role = st.selectbox("Access Level", ["User", "Admin"])
            if st.button("Authenticate", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.auth_status = True
                    st.session_state.user_role = role.lower()
                    st.rerun()
                except Exception as e:
                    st.error("Authentication failed. Please check credentials.")

        with choice[1]:
            new_email = st.text_input("Email Address", key="reg_email")
            new_pass = st.text_input("Set Password", type="password", key="reg_pass")
            if st.button("Create Account", use_container_width=True):
                try:
                    supabase.auth.sign_up({"email": new_email, "password": new_pass})
                    st.info("Registration request sent. Please attempt login.")
                except Exception as e:
                    st.error(f"Registration Error: {str(e)}")

# ---------------- MAIN APP ----------------
else:
    # Sidebar Styling
    st.sidebar.markdown(f"### System Access: **{st.session_state.user_role.upper()}**")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["Framework Generator", "Assessment History"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Termintate Session", use_container_width=True):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Framework Generator":
        st.header("Assessment Framework Generator")
        st.caption("Upload requirements to generate structured interview rubrics.")
        
        col_a, col_b = st.columns([2, 1])
        
        with col_a:
            uploaded_file = st.file_uploader("Job Description (Text File)", type=["txt"])
            jd = uploaded_file.read().decode("utf-8") if uploaded_file else st.text_area("Input Job Description", height=250)

        with col_b:
            st.subheader("Parameters")
            difficulty = st.select_slider("Candidate Seniority", options=["Junior", "Mid", "Senior"])
            cand_name = st.text_input("Candidate Full Name")
            
            st.markdown("Weightage Allocation")
            tech_w = st.slider("Technical Proficiency", 0, 100, 50)
            soft_w = 100 - tech_w
            st.caption(f"Soft Skills: {soft_w}%")

        if st.button("Generate Assessment Framework", use_container_width=True) and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            # Database Update
            history_entry = {
                "candidate_name": cand_name if cand_name else "N/A",
                "jd_role": f"{difficulty} Specialist",
                "total_score": float(tech_w),
                "created_by": st.session_state.user_role
            }
            supabase.table("candidate_results").insert(history_entry).execute()

            st.success("Framework successfully generated and archived.")
            
            # Simple Professional PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            content = [
                Paragraph(f"Interview Rubric: {cand_name}", styles["Title"]),
                Spacer(1, 12),
                Paragraph(f"Seniority Level: {difficulty}", styles["Normal"]),
                Spacer(1, 10),
                Paragraph("Targeted Assessment Questions:", styles["Heading3"])
            ]
            for q in questions:
                content.append(Paragraph(f"• {q}", styles["Normal"]))
            
            doc.build(content)
            
            st.download_button(
                label="Download Assessment PDF",
                data=buffer.getvalue(),
                file_name=f"Assessment_{cand_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    elif page == "Assessment History":
        st.header("Enterprise Audit Logs")
        try:
            res = supabase.table("candidate_results").select("*").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                st.dataframe(df[["candidate_name", "jd_role", "total_score", "created_by"]], use_container_width=True)
            else:
                st.info("No historical data available.")
        except:
            st.error("Unable to sync with cloud database.")