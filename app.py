import streamlit as st
import plotly.graph_objects as go

# Page Configuration
st.set_page_config(page_title="SkillSense AI", layout="wide")

# Sidebar
with st.sidebar:
    st.title("SkillSense AI")
    st.write("Role: **ADMIN**")
    st.radio("Navigation", ["Framework Generator", "Assessment History"])
    st.button("Logout")

# Main Content
st.header("Live Result Summary")

col1, col2 = st.columns([1, 1])

with col1:
    # Summary Card
    st.markdown("""
    <div style="background-color: #1e2630; padding: 20px; border-radius: 10px;">
        <h3>Candidate: john</h3>
        <h4>Role: Software Engineer</h4>
        <p>Targeting a <b>Junior-level Software Engineer</b> profile focusing on <b>General Technical</b>. 
        Expected match: <b>70%</b>.</p>
    </div>
    """, unsafe_allow_all_with_html=True)
    
    st.subheader("Detected Skills:")
    st.write("General Technical")
    
    st.subheader("Suggested Role:")
    st.write("Software Engineer")

with col2:
    # Donut Chart for Technical vs Soft Skills
    fig = go.Figure(data=[go.Pie(labels=['Technical', 'Soft Skills'], 
                             values=[70, 30], 
                             hole=.6,
                             marker_colors=['#63b3ed', '#2b6cb0'])])
    fig.update_layout(showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    # Metrics Progress Bars
    st.write(f"Culture Fit: 80%")
    st.progress(0.80)
    st.write(f"Tech Score: 70%")
    st.progress(0.70)
    st.write(f"Domain Fit: 85%")
    st.progress(0.85)

st.divider()

# Targeted Interview Questions Section (இதுதான் உங்களுக்கு மிஸ் ஆனது)
st.subheader("Targeted Interview Questions")

questions = [
    "**Technical:** Explain how you have handled debugging in a production environment with real-world systems?",
    "**System Design:** Given our focus on General Technical skills, how would you approach a bottleneck in a high-traffic system?",
    "**Culture/Domain:** With an 85% domain fit, how do you keep up with the latest trends in this specific industry?",
    "**Collaboration:** Describe a time you had to simplify a technical problem for a non-technical team member."
]

for q in questions:
    st.info(q)

# Overall Match Score Footer
st.markdown("<h2 style='text-align: center;'>OVERALL MATCH SCORE</h2>", unsafe_allow_all_with_html=True)
st.markdown("<h1 style='text-align: center; color: #63b3ed;'>70%</h1>", unsafe_allow_all_with_html=True)