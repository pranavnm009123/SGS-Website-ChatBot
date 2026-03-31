import os
from fpdf import FPDF

# Ensure the output directory exists
pdf_dir = os.path.join(os.path.dirname(__file__), "test_pdfs")
os.makedirs(pdf_dir, exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(w=0, h=10, text="ACME Corp - Confidential Document", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(w=0, h=10, text=f"Page {self.page_no()}", align="C")

documents = [
    {
        "filename": "ACME_Corp_Overview.pdf",
        "title": "ACME Corp Company Overview",
        "content": (
            "ACME Corp was founded in 2010 and has grown from a two-person startup into a "
            "global technology consultancy serving clients across 30 countries.\n\n"
            "Key Statistics:\n"
            "- Clients Served: 500+\n"
            "- Years in Business: 15\n"
            "- Team Members: 120+\n"
            "- Countries: 30\n\n"
            "Our mission is simple: help organizations harness the power of technology to do more, "
            "move faster, and create lasting impact."
        )
    },
    {
        "filename": "SLA_Starter_Plan.pdf",
        "title": "Service Level Agreement: Starter Plan",
        "content": (
            "This document outlines the Service Level Agreement (SLA) for the ACME Corp Starter Plan.\n\n"
            "Pricing: $5,000 / month\n\n"
            "Included Services:\n"
            "- Up to 2 dedicated engineers\n"
            "- Weekly check-ins\n"
            "- Email support\n"
            "- Basic CI/CD setup\n\n"
            "Support Response Time: Within 24 hours via email."
        )
    },
    {
        "filename": "SLA_Growth_Plan.pdf",
        "title": "Service Level Agreement: Growth Plan",
        "content": (
            "This document outlines the Service Level Agreement (SLA) for the ACME Corp Growth Plan.\n\n"
            "Pricing: $15,000 / month (Most Popular)\n\n"
            "Included Services:\n"
            "- Up to 6 dedicated engineers\n"
            "- Dedicated project manager\n"
            "- Slack + priority support\n"
            "- Full DevOps & cloud setup\n"
            "- Monthly strategy sessions\n\n"
            "Support Response Time: Within 4 hours via Slack."
        )
    },
    {
        "filename": "Case_Study_Cloud.pdf",
        "title": "Case Study: Global Cloud Migration",
        "content": (
            "Service Area: Cloud & Infrastructure\n\n"
            "Client Challenge: A multi-national retailer needed to scale their infrastructure "
            "for holiday traffic while reducing long-term costs.\n\n"
            "ACME Corp Solution: We architected a scalable, resilient cloud environment on AWS "
            "using Kubernetes and container orchestration. A CI/CD pipeline was set up to "
            "automate deployments.\n\n"
            "Results: Zero downtime during peak sales, 30% reduction in monthly cloud costs via FinOps."
        )
    },
    {
        "filename": "Case_Study_AI.pdf",
        "title": "Case Study: Generative AI Integration",
        "content": (
            "Service Area: AI & Machine Learning\n\n"
            "Client Challenge: A financial institution wanted to improve customer service "
            "response times and accuracy using their internal knowledge base.\n\n"
            "ACME Corp Solution: We implemented a RAG (Retrieval-Augmented Generation) knowledge "
            "system using state-of-the-art NLP and document intelligence.\n\n"
            "Results: Customer inquiries handled 40% faster, with a 25% increase in customer satisfaction."
        )
    },
    {
        "filename": "Cybersecurity_Framework.pdf",
        "title": "Cybersecurity Service Framework",
        "content": (
            "ACME Corp protects your digital assets through proactive security assessments, "
            "architecture reviews, and compliance planning.\n\n"
            "Our Core Security Offerings:\n"
            "1. Penetration Testing: Identifying vulnerabilities before they can be exploited.\n"
            "2. Zero-Trust Architecture: Ensuring internal and external threats are mitigated.\n"
            "3. SOC 2 & ISO 27001 Readiness: Helping your business meet global compliance standards.\n"
            "4. Incident Response Planning: Preparing your team for swift action in case of a breach."
        )
    },
    {
        "filename": "UX_Design_Process.pdf",
        "title": "UX & Product Design Methodology",
        "content": (
            "At ACME Corp, we create intuitive, beautiful experiences grounded in user research "
            "and accessibility best practices. Led by Carlos Rivera, Head of Design.\n\n"
            "Our Process incorporates:\n"
            "- UX Research & Journey Mapping: Understanding the user.\n"
            "- Wireframing & Prototyping: Rapid iteration.\n"
            "- Design Systems: Ensuring consistency across products.\n"
            "- Usability Testing: Validating designs with real users."
        )
    },
    {
        "filename": "Data_Architecture.pdf",
        "title": "Modern Data & Analytics Architecture",
        "content": (
            "ACME Corp turns raw data into strategic insights.\n\n"
            "Capabilities:\n"
            "- Data Warehouse Design: Scalable storage for all your enterprise data.\n"
            "- ETL / ELT Pipeline Engineering: Robust pipelines to move and transform data.\n"
            "- Business Intelligence Dashboards: Visualizing metrics that matter.\n"
            "- Real-Time Streaming Analytics: Acting on data as it arrives."
        )
    },
    {
        "filename": "Leadership_Profiles.pdf",
        "title": "ACME Corp Leadership Team Profiles",
        "content": (
            "The people guiding ACME Corp's vision and strategy:\n\n"
            "Sarah Mitchell - CEO & Co-Founder\n"
            "15 years in enterprise technology. Former VP at Salesforce.\n\n"
            "James Okafor - CTO & Co-Founder\n"
            "Distributed systems expert. Led platform engineering at Stripe.\n\n"
            "Priya Anand - VP of Product\n"
            "Product strategist passionate about user-centric design.\n\n"
            "Carlos Rivera - Head of Design\n"
            "Award-winning UX designer. Previously at IDEO and Google."
        )
    },
    {
        "filename": "Custom_Software_Lifecycle.pdf",
        "title": "Custom Software Development Lifecycle",
        "content": (
            "ACME Corp builds bespoke applications from the ground up - web, mobile, and desktop.\n\n"
            "Our Development Pillars:\n"
            "- Full-Stack Web Applications: Using modern frameworks.\n"
            "- Native & Cross-Platform Mobile: Reaching users anywhere.\n"
            "- API Design & Integration: Connecting disparate systems.\n"
            "- Legacy System Modernization: Bringing old systems up to date with zero downtime in transition."
        )
    }
]

for doc in documents:
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(w=0, h=10, text=doc["title"], new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 12)
    clean_content = doc["content"].replace("—", "-").replace("’", "'")
    pdf.multi_cell(w=0, h=10, text=clean_content)
    
    pdf_path = os.path.join(pdf_dir, doc["filename"])
    pdf.output(pdf_path)
    print(f"Generated {pdf_path}")

print("All 10 ACME Corp PDFs generated successfully.")
