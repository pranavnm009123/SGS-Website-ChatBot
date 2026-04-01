import os
import random
from fpdf import FPDF

# Ensure the output directory exists
pdf_dir = os.path.join(os.path.dirname(__file__), "test_pdfs")
os.makedirs(pdf_dir, exist_ok=True)

class PolicyPDF(FPDF):
    def header(self):
        self.set_left_margin(20)
        self.set_right_margin(20)
        self.set_font("helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(w=0, h=10, text="SGS Technologies - Internal Policy Framework", border=False, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 200)
        self.line(20, 18, 190, 18)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(w=0, h=10, text=f"Page {self.page_no()} of {{nb}}", align="C")

# --- Professional Content Bank ---

INTRO_PARAGRAPHS = [
    "This document establishes the official standards and operational guidelines for SGS Technologies. The primary objective is to align organizational practices with global best practices and legal mandates while ensuring a culture of excellence and accountability.",
    "The standards outlined herein serve as a foundational pillar for our operational integrity. This policy is designed to mitigate systemic risks, protect corporate assets, and ensure the sustained growth of the enterprise in a rapidly evolving market.",
]

SCOPE_PARAGRAPHS = [
    "This policy applies to all full-time and part-time employees, contractors, third-party vendors, and stakeholders interacting with SGS Technologies resources. It covers all geographical locations and operational jurisdictions.",
    "The scope of this framework encompasses all physical and digital assets, intellectual property, and proprietary data under the management or ownership of SGS Technologies. No exemptions are granted without written executive approval.",
]

POLICY_SECTIONS = [
    {
        "header": "1.0 Operational Excellence",
        "text": "Employees must adhere to the highest standards of professional conduct. This include maintaining meticulous records of all project interactions, adhering to the 'Agile First' delivery model, and ensuring that all client deliverables undergo multiple tiers of quality assurance before final sign-off."
    },
    {
        "header": "2.0 Data Protection and Information Security",
        "text": "Information security is a collective responsibility. All digital interactions must be encrypted via TLS 1.3, and multi-factor authentication (MFA) is mandatory for all internal systems. Unauthorized disclosure of proprietary information is strictly prohibited and subject to immediate disciplinary action."
    },
    {
        "header": "3.0 Ethical Conduct and Conflict of Interest",
        "text": "SGS Technologies is committed to a zero-tolerance policy regarding bribery, corruption, and unethical recruitment practices. Employees are required to disclose any potential conflicts of interest, including secondary employment or significant financial stakes in competing enterprises, on an annual basis."
    },
    {
        "header": "4.0 Workplace Health and Sustainable Environment",
        "text": "As part of our 2026 Sustainability Roadmap, we prioritize mental health and physical well-being. Flexible work arrangements are supported where operational needs permit. Furthermore, all physical offices must comply with ISO 14001 environmental management standards to minimize our carbon footprint."
    },
    {
        "header": "5.0 Compliance Monitoring and Audit Protocols",
        "text": "Internal audits will be conducted quarterly to ensure strict adherence to these frameworks. The Compliance Officer is granted full authority to investigate any deviations and report directly to the Board of Directors. Non-compliance results in tiered penalties ranging from formal warnings to contract termination."
    }
]

# --- Helper to add sections ---

def add_full_section(pdf, header, text):
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(40, 40, 100)
    pdf.multi_cell(w=pdf.epw, h=10, text=header)
    pdf.ln(2)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    # Add multiple filler paragraphs to make it "full"
    for _ in range(random.randint(2, 4)):
        pdf.multi_cell(w=pdf.epw, h=7, text=text)
        pdf.ln(3)
        # Add a bulleted list for detail
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(w=0, h=8, text="- Implementation Checkpoint:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", "", 11)
        checklist = ["Verification of compliance logs.", "Review of stakeholder feedback.", "Validation of resource allocation efficiency."]
        for item in checklist:
            pdf.cell(w=5, h=7, text=">>")
            pdf.multi_cell(w=pdf.epw-5, h=7, text=item)
        pdf.ln(5)
        pdf.set_font("helvetica", "", 12)

# --- Document Definitions ---

documents = [
    {"filename": "SGS_Strategic_Roadmap_2026.pdf", "title": "Strategic Operational Roadmap 2026"},
    {"filename": "SGS_Information_Security_Protocol.pdf", "title": "Comprehensive Information Security Protocol"},
    {"filename": "SGS_Employee_Excellence_Handbook.pdf", "title": "Employee Excellence & Conduct Handbook"},
    {"filename": "SGS_Vendor_Compliance_Manual.pdf", "title": "Vendor Compliance and Risk Management Manual"},
    {"filename": "SGS_Quality_Audit_Framework.pdf", "title": "Internal Quality Audit & Assurance Framework"},
    {"filename": "SGS_Data_Sovereignty_Policy.pdf", "title": "Global Data Sovereignty & Privacy Policy"},
    {"filename": "SGS_Disaster_Recovery_Plan.pdf", "title": "Corporate Disaster Recovery & Continuity Plan"},
    {"filename": "SGS_Cloud_Architecture_Standards.pdf", "title": "Cloud-Native Architecture & Scaling Standards"},
    {"filename": "SGS_Sustainable_Impact_Charter.pdf", "title": "Social Responsibility & Sustainable Impact Charter"},
    {"filename": "SGS_Technical_Debt_Guidelines.pdf", "title": "Guidelines for Technical Debt and Legacy Mitigation"}
]

# --- Main Generation Loop ---

for doc in documents:
    pdf = PolicyPDF()
    pdf.alias_nb_pages()
    
    # Random 5-10 pages, weighted to avg ~7
    page_count = random.choices(range(5, 11), weights=[1, 2, 4, 4, 2, 1])[0]
    for p in range(page_count):
        pdf.add_page()
        
        if p == 0:
            # Title Page styling
            pdf.ln(40)
            pdf.set_font("helvetica", "B", 26)
            pdf.set_text_color(50, 50, 150)
            pdf.multi_cell(w=pdf.epw, h=15, text=doc["title"], align="C")
            pdf.ln(10)
            pdf.set_font("helvetica", "I", 14)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(w=0, h=10, text="Official Executive Publication", align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(20)
            pdf.set_font("helvetica", "", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(w=pdf.epw, h=8, text=random.choice(INTRO_PARAGRAPHS))
            continue
        
        if p == 1:
            pdf.set_font("helvetica", "B", 16)
            pdf.cell(w=0, h=12, text="Scope of Authority", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.set_font("helvetica", "", 12)
            pdf.multi_cell(w=pdf.epw, h=8, text=random.choice(SCOPE_PARAGRAPHS))
            pdf.ln(10)
            add_full_section(pdf, "Executive Summary", "This framework serves as the comprehensive guide for our 2026 operations. It ensures that every team member is synchronized with our collective vision of providing world-class technological solutions.")
            continue
            
        # Distribute the 5 POLICY_SECTIONS over the remaining pages
        section_idx = (p - 2) % len(POLICY_SECTIONS)
        section = POLICY_SECTIONS[section_idx]
        add_full_section(pdf, section["header"], section["text"])

    pdf_path = os.path.join(pdf_dir, doc["filename"])
    pdf.output(pdf_path)
    print(f"Generated {doc['filename']} ({page_count} pages)")

print("\nSuccess: All 10 high-quality PDFs have been rebuilt and are available in backend/test_pdfs.")

