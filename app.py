import streamlit as st
from fpdf import FPDF
import io
import os

st.set_page_config(page_title="HR Intelligence Tool", layout="wide")

st.title("🤖 HR Intelligence Tool")
st.write("Upload Job Description → Generate HR-style PDF Report")

uploaded_files = st.file_uploader(
    "Upload Job Description files",
    type=["txt"],
    accept_multiple_files=True
)

# ---------- PDF CLASS ----------
class PDF(FPDF):
    def header(self):
        self.set_font("DejaVu", "", 14)
        self.cell(0, 10, "HR Intelligence Report", ln=True, align="C")
        self.ln(5)

# ---------- BUTTON ----------
if uploaded_files and st.button("Generate Report"):

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    font_path = "DejaVuSans.ttf"

    if not os.path.exists(font_path):
        st.error("❌ DejaVuSans.ttf not found in repo root!")
        st.stop()

    pdf.add_font("DejaVu", "", font_path, uni=True)
    pdf.set_font("DejaVu", "", 11)

    for idx, file in enumerate(uploaded_files, start=1):

        jd_text = file.read().decode("utf-8", errors="ignore")

        pdf.add_page()

        page_width = pdf.w - 2 * pdf.l_margin

        pdf.set_font("DejaVu", "", 13)
        pdf.cell(0, 10, f"Job Description #{idx}", ln=True)

        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(page_width, 7, jd_text or "No JD provided.")

        pdf.ln(4)

        # ---- Sample AI Questions ----
        pdf.set_font("DejaVu", "", 12)
        pdf.cell(0, 10, "Suggested Interview Questions:", ln=True)

        questions = [
            "Explain a challenging project you handled.",
            "What technical tools are you strongest in?",
            "How do you debug production issues?",
            "How do you handle deadlines?",
        ]

        pdf.set_font("DejaVu", "", 11)

        for q in questions:
            pdf.multi_cell(page_width, 7, f"- {q}")

    # -------- SAVE TO BYTES --------
    pdf_bytes = pdf.output(dest="S")

    buffer = io.BytesIO(pdf_bytes)

    st.success("✅ PDF generated successfully!")

    st.download_button(
        "📥 Download PDF",
        data=buffer,
        file_name="HR_Report.pdf",
        mime="application/pdf"
    )
