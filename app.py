import streamlit as st
import pandas as pd
from supabase import create_client
import io
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------- CONFIG ----------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "sb_publishable_GhOIaGz64kXAeqLpl2c4wA_x8zmE_Mr"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="HR Intel Portal", layout="wide")

# Session State Init
if "auth_status" not in st.session_state:
    st.session_state.auth_status = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None

# ---------------- CORE LOGIC ----------------
SKILL_DB = {
    "python": "Python", "sql": "SQL", "docker": "Docker", 
    "kubernetes": "Kubernetes", "aws": "AWS", "azure": "Azure",
    "react": "React", "machine learning": "ML", "data analysis": "Data",
    "devops": "DevOps", "ci/cd": "CI/CD", "terraform": "Terraform", "linux": "Linux",
}

def extract_skills(text):
    found = [v for k, v in SKILL_DB.items() if k in text.lower()]
    return list(set(found))

def generate_questions(skills, level):
    qs = []
    for s in skills:
        if level == "Junior": qs.append(f"Explain foundational concepts of {s} and practical implementation.")
        elif level == "Mid": qs.append(f"Discuss implementation strategies and troubleshooting for {s}.")
        else: qs.append(f"Describe architectural decision-making and optimization using {s}.")
    return qs

# ---------------- AUTH UI (Fixed 2-times click issue) ----------------
if not st.session_state.auth_status:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<h1 style='text-align: center;'>HR Intelligence Portal</h1>", unsafe_allow_html=True)
        st.markdown("---")
        # Form helps to process login in one click
        with st.form("login_form"):
            email = st.text_input("Corporate Email")
            password = st.text_input("Password", type="password")
            role_choice = st.selectbox("Login as", ["Admin", "User"])
            if st.form_submit_button("Authenticate", use_container_width=True):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state.auth_status = True
                        st.session_state.user_role = role_choice
                        st.rerun() # Immediate redirect
                except:
                    st.error("Login failed. Check credentials.")

# ---------------- MAIN APP (UI kept exactly as you liked) ----------------
else:
    st.sidebar.markdown(f"### Role: **{st.session_state.user_role.upper()}**")
    nav_options = ["Framework Generator"]
    if st.session_state.user_role == "Admin": 
        nav_options.append("Assessment History")
    
    page = st.sidebar.radio("Navigation", nav_options)
    
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.auth_status = False
        st.rerun()

    if page == "Framework Generator":
        st.header("Evaluation Framework")
        c1, c2 = st.columns([1.5, 1])
        with c1: 
            jd = st.text_area("Input Job Description", height=250)
        with c2:
            cand_name = st.text_input("Candidate Name")
            difficulty = st.select_slider("Level", options=["Junior", "Mid", "Senior"])
            tech_w = st.slider("Technical Weight (%)", 0, 100, 70)
            soft_w = 100 - tech_w

        if st.button("Process Assessment", use_container_width=True) and jd:
            skills = extract_skills(jd)
            questions = generate_questions(skills, difficulty)
            
            # --- UI Results Section ---
            st.divider()
            r1, r2 = st.columns(2)
            with r1:
                st.subheader("Live Summary")
                st.write(f"**Candidate:** {cand_name if cand_name else 'N/A'}")
                st.write(f"**Competencies Identified:** {', '.join(skills) if skills else 'N/A'}")
            with r2:
                # Pie Chart
                fig = go.Figure(data=[go.Pie(
                    labels=['Technical', 'Soft Skills'], 
                    values=[tech_w, soft_w], 
                    hole=.4,
                    marker_colors=['#1E3A8A', '#94A3B8']
                )])
                fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=220)
                st.plotly_chart(fig, use_container_width=True)

            # Questions display in UI
            for i, q in enumerate(questions, 1): 
                st.info(f"{i}. {q}")

            # --- PDF GENERATION (Fixed Blank Issue) ---
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Professional Styles
            title_style = ParagraphStyle('T', parent=styles['Title'], textColor=colors.HexColor("#1E3A8A"), spaceAfter=12)
            head_style = ParagraphStyle('H', parent=styles['Heading2'], textColor=colors.HexColor("#2563EB"), spaceBefore=10)
            
            pdf_elements = []
            pdf_elements.append(Paragraph("CANDIDATE ASSESSMENT REPORT", title_style))
            pdf_elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=15))
            
            # Summary Table in PDF
            summary_data = [
                ["Candidate Name:", cand_name if cand_name else "N/A"],
                ["Level:", difficulty],
                ["Technical Weight:", f"{tech_w}%"],
                ["Soft Skills Weight:", f"{soft_w}%"]
            ]
            tbl = Table(summary_data, colWidths=[150, 300])
            tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
                ('PADDING', (0,0), (-1,-1), 6)
            ]))
            pdf_elements.append(tbl)
            pdf_elements.append(Spacer(1, 15))

            pdf_elements.append(Paragraph("IDENTIFIED COMPETENCIES", head_style))
            pdf_elements.append(Paragraph(", ".join(skills) if skills else "N/A", styles['Normal']))
            pdf_elements.append(Spacer(1, 10))
            
            pdf_elements.append(Paragraph("STRUCTURED INTERVIEW QUESTIONS", head_style))
            for i, q in enumerate(questions, 1):
                pdf_elements.append(Paragraph(f"<b>{i}.</b> {q}", styles['Normal']))
                pdf_elements.append(Spacer(1, 6))

            # Important: Build the PDF into the buffer
            doc.build(pdf_elements)
            
            # Display download button
            st.download_button(
                label="📥 Download Detailed PDF Report",
                data=buffer.getvalue(),
                file_name=f"Report_{cand_name}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            # Sync to Database
            try:
                supabase.table("candidate_results").insert({
                    "candidate_name": cand_name, 
                    "jd_role": f"{difficulty} Specialist",
                    "total_score": float(tech_w), 
                    "created_by": st.session_state.user_role
                }).execute()
            except: pass

    elif page == "Assessment History":
        st.header("Enterprise Audit Logs")
        try:
            res = supabase.table("candidate_results").select("*").execute()
            st.dataframe(pd.DataFrame(res.data), use_container_width=True)
        except:
            st.error("Could not fetch history from database.")