import streamlit as st
from supabase import create_client
import pandas as pd
import re

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, ListFlowable, ListItem
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# -----------------------------
# STREAMLIT TEST MARK
# -----------------------------
st.write("🔥 NEW VERSION LOADED 🔥")


# -----------------------------
# SUPABASE CONFIG
# -----------------------------
SUPABASE_URL = "https://cgzvvhlrdffiyswgnmpp.supabase.co"
SUPABASE_KEY = "YOUR_KEY_HERE"   # move to .env later

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------
# SESSION INIT
# -----------------------------
for key in ["skills", "questions", "cand_name", "tech_w", "soft_w"]:
    if key not in st.session_state:
        st.session_state[key] = None


# -----------------------------
# UI INPUTS
# -----------------------------
st.title("HR Intelligence Tool")

cand_name = st.text_input("Candidate Name")
jd = st.text_area("Paste Job Description")

difficulty = st.selectbox(
    "Difficulty",
    ["Easy", "Medium", "Hard"]
)

tech_w = st.slider("Technical Weight %", 0, 100, 70)
soft_w = 100 - tech_w


# -----------------------------
# PROCESS BUTTON (FIXED)
# -----------------------------
if st.button("Process Assessment", use_container_width=True) and jd:

    st.session_state.skills = extract_skills(jd)
    st.session_state.questions = generate_questions(
        st.session_state.skills,
        difficulty
    )

    st.session_state.cand_name = cand_name
    st.session_state.tech_w = tech_w
    st.session_state.soft_w = soft_w


# -----------------------------
# RESULTS AREA
# -----------------------------
if st.session_state.skills:

    st.divider()

    st.subheader("📊 Assessment Summary")

    st.write("Candidate:", st.session_state.cand_name)
    st.write("Skills:", ", ".join(st.session_state.skills))

    st.write("Tech Weight:", st.session_state.tech_w)
    st.write("Soft Weight:", st.session_state.soft_w)

    st.subheader("❓ Interview Questions")

    for q in st.session_state.questions:
        st.markdown(f"- {q}")
