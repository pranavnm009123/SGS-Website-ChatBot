import os
import random
from fpdf import FPDF

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


# ---------------------------------------------------------------------------
# Each document has its own UNIQUE sections. No text is shared between docs.
# ---------------------------------------------------------------------------

DOCUMENTS = [
    {
        "filename": "SGS_Strategic_Roadmap_2026.pdf",
        "title": "Strategic Operational Roadmap 2026",
        "sections": [
            ("1.0 Market Expansion Strategy",
             "SGS Technologies will expand into three new geographic markets in 2026: Southeast Asia, Eastern Europe, and Latin America. Each region will have a dedicated Country Manager reporting to the VP of Global Operations. Market entry will follow a phased approach: Phase 1 involves establishing legal entities and hiring local talent within 90 days. Phase 2 focuses on securing anchor clients through targeted account-based marketing. Phase 3 scales the team to 25+ engineers per region by Q4 2026."),
            ("2.0 Quarterly KPI Framework",
             "All business units must track and report on the following KPIs quarterly: Customer Acquisition Cost (CAC) must remain below $12,000 per enterprise client. Monthly Recurring Revenue (MRR) growth must exceed 8% quarter-over-quarter. Employee Net Promoter Score (eNPS) must maintain a minimum of 45. Engineering velocity is measured in story points per sprint, with a target of 85+ per team. Customer churn rate must stay below 3% annually."),
            ("3.0 Innovation Pipeline",
             "The Innovation Lab will receive 15% of annual R&D budget, approximately $4.2 million, to explore emerging technologies. Current pipeline priorities include: a real-time language translation engine for multilingual support platforms, an edge computing framework for IoT-heavy manufacturing clients, and a predictive maintenance system using federated machine learning. Each project undergoes a Stage-Gate review every 6 weeks with the CTO and VP of Engineering."),
            ("4.0 Strategic Partnership Targets",
             "SGS will pursue Platinum-tier partnerships with AWS, Microsoft Azure, and Google Cloud by demonstrating 50+ certified engineers per platform. Additionally, the company will establish co-selling agreements with Salesforce for CRM integration projects and with Snowflake for data warehouse migrations. Partnership revenue is expected to contribute 22% of total revenue by end of 2026."),
            ("5.0 Financial Projections and Budget Allocation",
             "Total projected revenue for FY2026 is $38.7 million, representing a 31% increase over FY2025. Budget allocation: Engineering 42%, Sales & Marketing 28%, Operations 18%, R&D 12%. Capital expenditure includes $1.8 million for new office buildouts in Austin and Bangalore. The company targets EBITDA margin improvement from 16% to 21% through operational efficiency gains and automation of internal processes."),
        ]
    },
    {
        "filename": "SGS_Information_Security_Protocol.pdf",
        "title": "Comprehensive Information Security Protocol",
        "sections": [
            ("1.0 Network Security Architecture",
             "All SGS production environments must implement a defense-in-depth architecture consisting of: perimeter firewalls with stateful packet inspection, internal network segmentation using VLANs with micro-segmentation policies, intrusion detection and prevention systems (IDS/IPS) monitored by the Security Operations Center (SOC) 24/7, and web application firewalls (WAF) protecting all public-facing services. Network traffic between data centers must traverse encrypted IPsec VPN tunnels with AES-256 encryption."),
            ("2.0 Access Control and Identity Management",
             "All employees must authenticate through the centralized Okta SSO platform with mandatory multi-factor authentication (MFA) using hardware security keys (YubiKey 5 or equivalent). Password requirements: minimum 16 characters, must include uppercase, lowercase, numbers, and special characters, with rotation every 90 days. Service accounts require API key rotation every 30 days. Privileged access to production systems requires additional approval through the PAM (Privileged Access Management) system with session recording enabled."),
            ("3.0 Vulnerability Management Program",
             "Automated vulnerability scans using Qualys must run weekly against all production assets. Critical vulnerabilities (CVSS score 9.0+) must be patched within 48 hours. High severity (CVSS 7.0-8.9) within 7 days. Medium severity within 30 days. Third-party penetration testing by an independent firm (currently NCC Group) is conducted bi-annually. All findings are tracked in Jira with mandatory root cause analysis for any Critical finding."),
            ("4.0 Data Encryption Standards",
             "Data at rest must be encrypted using AES-256. Data in transit must use TLS 1.3 exclusively; TLS 1.2 is permitted only for legacy integrations with documented exception approval from the CISO. Database-level encryption is mandatory using Transparent Data Encryption (TDE) for SQL databases and field-level encryption for PII in NoSQL stores. Encryption keys are managed through AWS KMS with automatic key rotation every 365 days. Key access is audited monthly."),
            ("5.0 Security Incident Classification",
             "Security incidents are classified into four severity tiers: SEV-1 (Critical) includes active data breaches, ransomware, or compromise of production systems  --  response time is 15 minutes with mandatory executive notification. SEV-2 (High) includes unauthorized access attempts or malware detection  --  response time is 1 hour. SEV-3 (Medium) includes policy violations or suspicious activity  --  response within 4 hours. SEV-4 (Low) includes informational events or false positives  --  response within 24 hours."),
        ]
    },
    {
        "filename": "SGS_Employee_Excellence_Handbook.pdf",
        "title": "Employee Excellence & Conduct Handbook",
        "sections": [
            ("1.0 Onboarding and Probation",
             "New employees undergo a structured 90-day onboarding program. Week 1 covers HR orientation, IT setup, and security training. Weeks 2-4 involve shadowing senior team members and completing role-specific certification paths. The probation period is 6 months, during which performance reviews occur at Day 30, Day 60, and Day 90. A final probation review with the hiring manager and HR determines full-time conversion. During probation, the notice period is 2 weeks for both parties."),
            ("2.0 Compensation and Benefits Structure",
             "SGS offers a competitive total compensation package. Base salary is benchmarked at the 75th percentile of market rates using Radford survey data. Annual performance bonuses range from 5% to 20% of base salary based on individual and company performance. Benefits include: 100% employer-paid health, dental, and vision insurance for employees (75% for dependents), a 401(k) match of 4%, $5,000 annual learning stipend, 20 days PTO plus 10 company holidays, and 16 weeks paid parental leave."),
            ("3.0 Remote Work and Flexible Schedule Policy",
             "SGS operates on a hybrid-flexible model. Engineers and product teams may work fully remote with quarterly on-site weeks. Client-facing roles require a minimum of 3 days per week in-office or at client sites. Core collaboration hours are 10 AM to 3 PM in the employee's local time zone. International travel for client engagements requires VP-level approval and a minimum 2-week advance notice. Home office stipend of $1,500 is provided upon hire for equipment setup."),
            ("4.0 Performance Review Cycle",
             "Performance evaluations follow a biannual cadence: Mid-Year Review in June and Annual Review in December. Reviews use a 5-point rating scale: Exceptional (5), Exceeds Expectations (4), Meets Expectations (3), Needs Improvement (2), and Unsatisfactory (1). Employees rated 2 or below are placed on a 60-day Performance Improvement Plan (PIP). Promotion eligibility requires a minimum rating of 4 in two consecutive review cycles. 360-degree feedback is collected from peers, direct reports, and cross-functional partners."),
            ("5.0 Code of Conduct and Anti-Harassment",
             "SGS maintains zero tolerance for harassment, discrimination, and retaliation. All employees complete mandatory anti-harassment training within 30 days of hire and annually thereafter. Reports can be filed through the anonymous Ethics Hotline (1-800-555-ETHICS), direct manager, HR Business Partner, or the online reporting portal. Investigations are completed within 15 business days. Substantiated claims result in disciplinary action up to and including termination. Retaliation against reporters is a terminable offense."),
        ]
    },
    {
        "filename": "SGS_Vendor_Compliance_Manual.pdf",
        "title": "Vendor Compliance and Risk Management Manual",
        "sections": [
            ("1.0 Vendor Classification and Tiering",
             "All vendors are classified into three tiers based on risk exposure. Tier 1 (Critical): vendors with access to production systems or customer data, including cloud providers, payment processors, and managed security services  --  these undergo annual SOC 2 Type II audit review and quarterly business reviews. Tier 2 (Important): vendors providing development tools, communication platforms, or staffing services  --  reviewed bi-annually. Tier 3 (Standard): office supplies, facilities, and non-technical services  --  reviewed at contract renewal."),
            ("2.0 Procurement Workflow",
             "All vendor engagements exceeding $25,000 annually require a formal RFP process with a minimum of three competitive bids. The Procurement Committee (VP Finance, VP Engineering, Legal Counsel) evaluates proposals using a weighted scoring matrix: technical capability (35%), cost (25%), security posture (20%), references (10%), and cultural fit (10%). Contracts exceeding $100,000 require CEO approval. All vendor contracts must include a Right to Audit clause, data processing addendum, and 90-day termination notice period."),
            ("3.0 Vendor Security Assessment",
             "Before onboarding, all Tier 1 and Tier 2 vendors must complete the SGS Vendor Security Questionnaire (VSQ), a 147-question assessment covering: data handling practices, encryption standards, employee background check procedures, incident response capabilities, and business continuity planning. Vendors handling PII must demonstrate SOC 2 Type II compliance or equivalent (ISO 27001). Vendors failing the VSQ may undergo a remediation period of up to 60 days before re-assessment."),
            ("4.0 SLA Enforcement and Penalties",
             "Each vendor contract defines specific Service Level Agreements with financial penalties for non-compliance. Standard SLA metrics include: system uptime of 99.95% (measured monthly), mean time to respond (MTTR) of 15 minutes for critical issues, and mean time to resolve (MTTR) of 4 hours. Breach of SLA triggers a tiered penalty structure: first breach results in a 5% service credit, second breach in 10%, third breach triggers a formal vendor review and potential contract termination. All SLA performance data is tracked in the Vendor Management Dashboard."),
            ("5.0 Vendor Offboarding and Data Return",
             "When a vendor relationship ends, a structured offboarding process must be completed within 30 days. This includes: revocation of all system access and API keys within 24 hours of termination notice, return or certified destruction of all SGS data within 14 days (with a signed Certificate of Destruction), decommissioning of any dedicated environments, and final invoice reconciliation. The Legal team verifies compliance with contractual data return obligations. A post-mortem review documents lessons learned for future vendor selections."),
        ]
    },
    {
        "filename": "SGS_Quality_Audit_Framework.pdf",
        "title": "Internal Quality Audit & Assurance Framework",
        "sections": [
            ("1.0 Testing Methodology and Coverage Requirements",
             "All software releases must achieve minimum test coverage thresholds: 80% unit test coverage for backend services, 70% for frontend components, and 100% coverage for payment processing and authentication modules. Testing methodologies include: unit testing (Jest, pytest), integration testing (Postman collections, contract tests), end-to-end testing (Cypress, Playwright), and performance testing (k6, Locust). Test cases must be peer-reviewed before merging to the main branch."),
            ("2.0 Defect Tracking and Severity Classification",
             "All defects are tracked in Jira using the following severity classification: Blocker  --  system is completely non-functional or data loss is occurring (must fix within 4 hours). Critical  --  major feature is broken with no workaround (fix within 24 hours). Major  --  feature is impaired but a workaround exists (fix within 1 sprint). Minor  --  cosmetic issues or minor UX problems (fix within 2 sprints). Trivial  --  documentation typos or non-user-facing issues (fix when capacity allows). Zero open Blockers or Criticals are required for any production release."),
            ("3.0 Release Sign-Off Process",
             "Production releases follow a gated approval process. Gate 1: All automated tests pass in the CI pipeline with zero failures. Gate 2: QA Lead signs off on the test report confirming test plan completion and coverage targets. Gate 3: Product Owner approves the release notes and confirms feature acceptance. Gate 4: Security scan (Snyk, SonarQube) shows zero critical or high vulnerabilities. Gate 5: Release Manager coordinates the deployment window and rollback plan. Emergency hotfixes skip Gates 2-3 but require retroactive sign-off within 48 hours."),
            ("4.0 Code Review Standards",
             "Every code change requires approval from at least two reviewers before merging. Reviewers must include at least one Senior Engineer or Tech Lead. Review criteria include: adherence to the SGS Style Guide, appropriate error handling and logging, absence of hardcoded secrets or credentials, adequate test coverage for new logic, and performance implications for database queries. Reviews must be completed within 2 business days of submission. Pull requests exceeding 500 lines of code should be decomposed into smaller, reviewable units."),
            ("5.0 Post-Release Monitoring Protocol",
             "After every production deployment, a 72-hour monitoring window is mandatory. During this window, the on-call engineer monitors: error rates (must not exceed 0.1% increase over baseline), p99 latency (must not exceed 15% increase), CPU and memory utilization, and business metrics (conversion rates, transaction volumes). If any threshold is breached, an automatic rollback is triggered. Post-deployment retrospectives are conducted within one week of every major release, documenting what went well, what could improve, and action items."),
        ]
    },
    {
        "filename": "SGS_Data_Sovereignty_Policy.pdf",
        "title": "Global Data Sovereignty & Privacy Policy",
        "sections": [
            ("1.0 Data Residency Requirements",
             "Customer data must be stored in the same geographic region as the customer's primary business operations. SGS operates data centers in three regions: US-East (Virginia), EU-West (Frankfurt), and APAC (Singapore). Cross-region data transfer is prohibited without explicit customer consent and a signed Data Processing Addendum (DPA). US government client data must reside exclusively in FedRAMP-authorized US data centers with no foreign national access."),
            ("2.0 GDPR Compliance Framework",
             "For all EU-based customers and data subjects, SGS complies with the General Data Protection Regulation (GDPR). Key obligations: Data Subject Access Requests (DSARs) must be fulfilled within 30 calendar days. Right to Erasure requests require complete data deletion within 72 hours, including backups within 30 days. Data Protection Impact Assessments (DPIAs) are mandatory for any new processing activity involving personal data at scale. The appointed Data Protection Officer (DPO) is Sarah Chen, reachable at dpo@sgstech.com."),
            ("3.0 CCPA and US State Privacy Laws",
             "SGS complies with the California Consumer Privacy Act (CCPA) and its amendments under CPRA. California residents have the right to: know what personal information is collected and how it is used, delete their personal information, opt out of the sale or sharing of personal information, and non-discrimination for exercising their rights. SGS also monitors and complies with emerging state privacy legislation in Virginia (VCDPA), Colorado (CPA), Connecticut (CTDPA), and Texas (TDPSA). Compliance checklists are updated quarterly by the Legal team."),
            ("4.0 Data Retention and Disposal Schedule",
             "Data retention periods are defined by category: Active customer data is retained for the duration of the contract plus 12 months. Financial records and invoices are retained for 7 years per IRS requirements. Employee records are retained for 5 years post-termination. Server logs and audit trails are retained for 3 years. Marketing analytics data is retained for 2 years. Upon expiration, data must be destroyed using NIST 800-88 compliant methods. Quarterly disposal reports are submitted to the Compliance team for audit purposes."),
            ("5.0 Breach Notification Obligations",
             "In the event of a data breach involving personal data, SGS follows a strict notification timeline. Internal escalation to the CISO and Legal team must occur within 1 hour of discovery. For GDPR-covered breaches: the supervisory authority must be notified within 72 hours, and affected data subjects must be notified without undue delay if the breach poses high risk. For US breaches: notification follows state-specific timelines (most require notification within 60 days). All breach notifications include: nature of the breach, categories of data affected, estimated number of individuals impacted, measures taken to address the breach, and contact information for further inquiries."),
        ]
    },
    {
        "filename": "SGS_Disaster_Recovery_Plan.pdf",
        "title": "Corporate Disaster Recovery & Continuity Plan",
        "sections": [
            ("1.0 Recovery Time and Point Objectives",
             "SGS defines recovery targets by system criticality. Tier 1 (Mission-Critical) systems including payment processing, authentication, and core APIs: Recovery Time Objective (RTO) is 1 hour and Recovery Point Objective (RPO) is 15 minutes. Tier 2 (Business-Critical) systems including CRM, project management, and internal communications: RTO is 4 hours, RPO is 1 hour. Tier 3 (Business-Supporting) systems including HR portals, marketing tools, and analytics dashboards: RTO is 24 hours, RPO is 4 hours."),
            ("2.0 Failover Architecture",
             "All Tier 1 services operate in an active-active configuration across two AWS regions (us-east-1 and eu-west-1). Database replication uses synchronous multi-AZ replication with asynchronous cross-region replication for disaster recovery. DNS failover is managed through Route 53 health checks with automated failover triggered when three consecutive health checks fail (30-second intervals). Load balancers maintain connection draining for 300 seconds during failover to minimize dropped requests."),
            ("3.0 Backup Procedures and Verification",
             "Automated backups follow a 3-2-1 strategy: 3 copies of all data, on 2 different storage types (EBS snapshots and S3 cross-region), with 1 copy in an offline or air-gapped vault. Database backups run every 6 hours with transaction log backups every 15 minutes. File system backups run nightly. Backup integrity is verified through automated restoration tests conducted weekly on a dedicated recovery environment. Monthly backup restoration drills are documented and reviewed by the Infrastructure team lead."),
            ("4.0 Disaster Recovery Drills",
             "Full disaster recovery drills are conducted quarterly. Each drill simulates a complete regional outage and tests the following: automated failover to the secondary region, data integrity verification post-failover, application functionality validation through the full regression test suite, communication protocol execution (PagerDuty escalation, Slack war room, customer status page updates), and failback procedures to the primary region. Drill results are graded on a pass/fail basis, and any failures require a remediation plan completed within 2 weeks."),
            ("5.0 Business Continuity for Personnel",
             "In the event of a facility-level disaster (natural disaster, power outage, or pandemic), all employees transition to remote work within 2 hours. The Emergency Response Team (ERT), led by the VP of Operations, activates the communication tree via PagerDuty and mass SMS. Critical business functions maintain documented succession plans: each VP designates a primary and secondary successor. Payroll continuity is ensured through Gusto's multi-region infrastructure. The company maintains a 6-month operating expense reserve ($4.8 million) for business continuity."),
        ]
    },
    {
        "filename": "SGS_Cloud_Architecture_Standards.pdf",
        "title": "Cloud-Native Architecture & Scaling Standards",
        "sections": [
            ("1.0 Container Orchestration Standards",
             "All production workloads must be containerized using Docker and orchestrated through Amazon EKS (Elastic Kubernetes Service). Container images must be stored in Amazon ECR with image scanning enabled. Base images must use the SGS-approved hardened images (based on Distroless or Alpine). Pod resource requests and limits must be defined for all deployments: CPU requests at 250m with limits at 1000m, memory requests at 256Mi with limits at 1Gi. Horizontal Pod Autoscaler (HPA) must be configured with target CPU utilization of 70%."),
            ("2.0 Auto-Scaling and Capacity Planning",
             "Services must implement both horizontal and vertical auto-scaling. Horizontal scaling is managed through Kubernetes HPA with a minimum of 3 replicas and a maximum of 50 replicas per service. Scale-up threshold is 70% CPU or 80% memory utilization. Scale-down occurs after 5 minutes of utilization below 30%. Cluster auto-scaling uses Karpenter with provisioner limits of 200 nodes. Capacity planning reviews are conducted monthly, and load testing using k6 is required before any expected traffic spike exceeding 2x baseline."),
            ("3.0 Database Architecture Patterns",
             "Primary databases use Amazon RDS for PostgreSQL (version 15+) with Multi-AZ deployment. Read replicas are deployed in each region for read-heavy workloads. Connection pooling is mandatory using PgBouncer with a maximum of 100 connections per service. For high-throughput key-value workloads, Amazon DynamoDB is the approved solution with on-demand capacity mode. Caching layers use Amazon ElastiCache for Redis with cluster mode enabled. Cache TTL policies must be documented per service, with a default TTL of 300 seconds."),
            ("4.0 CI/CD Pipeline Requirements",
             "All services must deploy through the standardized CI/CD pipeline built on GitHub Actions. Pipeline stages: (1) Lint and static analysis (ESLint, Ruff), (2) Unit and integration tests with coverage reporting, (3) Container image build and security scan (Trivy), (4) Deployment to staging environment with automated smoke tests, (5) Manual approval gate for production, (6) Blue-green deployment to production with automatic rollback on health check failure. Deployment frequency target: multiple times per day for microservices, weekly for platform services. Mean Lead Time for Changes must be under 24 hours."),
            ("5.0 Observability and Monitoring Stack",
             "The standard observability stack consists of: Datadog for infrastructure and APM monitoring with custom dashboards per service, PagerDuty for alert management with escalation policies (L1 on-call responds within 5 minutes, L2 within 15 minutes), Sentry for error tracking with a target of zero unresolved P0 errors, and OpenTelemetry for distributed tracing across all microservices. Every service must expose a /health endpoint returning structured JSON with dependency status. SLO targets: 99.95% availability, p99 latency under 500ms for API endpoints."),
        ]
    },
    {
        "filename": "SGS_Sustainable_Impact_Charter.pdf",
        "title": "Social Responsibility & Sustainable Impact Charter",
        "sections": [
            ("1.0 Carbon Neutrality Commitment",
             "SGS Technologies commits to achieving net-zero carbon emissions by 2030. Current initiatives include: 100% renewable energy procurement for all office locations through renewable energy certificates (RECs), migration of all workloads to AWS regions powered by renewable energy, a corporate travel policy requiring carbon offset purchases for all flights (currently at $25 per ton of CO2), and a target to reduce Scope 1 and 2 emissions by 50% by 2028 against the 2023 baseline. Annual carbon footprint reports are published in our ESG disclosure and verified by an independent auditor."),
            ("2.0 Diversity, Equity, and Inclusion Metrics",
             "SGS tracks DEI metrics quarterly with the following 2026 targets: overall workforce gender diversity of 40% women and non-binary individuals (current: 34%), leadership representation (Director+) of 35% underrepresented minorities (current: 28%), pay equity gap of less than 2% across gender and ethnicity (current: 3.1%), and employee resource group (ERG) participation of 30%+ of workforce. The DEI Council, chaired by the Chief People Officer, meets monthly to review progress. Hiring panels must include at least one member from an underrepresented group."),
            ("3.0 Community Engagement Program",
             "Each employee receives 24 hours of paid volunteer time annually (3 full days) through the SGS Gives Back program. The company matches charitable donations up to $2,000 per employee per year. SGS partners with Code.org to deliver free coding workshops in underserved school districts, targeting 500 student interactions per quarter. The annual SGS Hackathon for Good dedicates 48 hours to building technology solutions for nonprofit partners, with winning projects receiving $50,000 in development resources to bring them to production."),
            ("4.0 Sustainable Procurement Standards",
             "All procurement decisions for office supplies, equipment, and facilities services must prioritize vendors with demonstrated sustainability practices. Evaluation criteria include: environmental certifications (ISO 14001, B Corp), use of recycled or sustainably sourced materials, carbon-neutral shipping options, and fair labor certifications. Single-use plastics are prohibited in all SGS offices. Electronics procurement must follow EPEAT Gold or equivalent standards. End-of-life electronics are recycled through certified e-waste processors with documented chain of custody."),
            ("5.0 Annual ESG Reporting",
             "SGS publishes an annual Environmental, Social, and Governance (ESG) report following the Global Reporting Initiative (GRI) Standards framework. The report covers: Scope 1, 2, and 3 greenhouse gas emissions, water usage and waste diversion rates, workforce demographics and DEI progress, community investment and volunteer hours, governance structure and board diversity, and supply chain sustainability assessments. The report is reviewed by the Board of Directors and made publicly available on the SGS investor relations page. Third-party assurance is provided by Deloitte."),
        ]
    },
    {
        "filename": "SGS_Technical_Debt_Guidelines.pdf",
        "title": "Guidelines for Technical Debt and Legacy Mitigation",
        "sections": [
            ("1.0 Technical Debt Classification System",
             "SGS classifies technical debt into four categories: Architecture Debt  --  fundamental design flaws requiring system restructuring (e.g., monolith-to-microservice migration). Code Debt  --  suboptimal code patterns, duplicated logic, or missing abstractions. Dependency Debt  --  outdated libraries, unsupported frameworks, or end-of-life runtime versions. Test Debt  --  insufficient test coverage, flaky tests, or missing integration test suites. Each category is scored on a severity scale of 1-5 using the SQALE methodology, and scores are tracked in the SGS Tech Health Dashboard."),
            ("2.0 Sprint Allocation for Debt Reduction",
             "Each engineering team must allocate a minimum of 20% of sprint capacity to technical debt reduction. This translates to approximately 2 days per developer per sprint. Debt reduction work is tracked through dedicated Jira epics tagged with the 'tech-debt' label. Sprint planning must include at least one tech debt story. During the annual Tech Debt Week (held in March), all teams focus exclusively on debt reduction with a target of resolving at least 30% of accumulated high-severity items. Progress is reported to the CTO in monthly engineering reviews."),
            ("3.0 Dependency Management and Upgrade Policy",
             "All project dependencies must be tracked using Dependabot or Renovate for automated update notifications. Security patches for dependencies must be applied within 72 hours of release. Major version upgrades must be completed within 90 days of the library's release to avoid falling behind. End-of-life (EOL) runtimes and frameworks must be migrated before the EOL date with a 6-month buffer. Currently tracked EOL milestones: Node.js 18 LTS (April 2025 - COMPLETED), Python 3.9 (October 2025 - IN PROGRESS), React 17 (December 2025 - PLANNED)."),
            ("4.0 Legacy System Migration Playbook",
             "Legacy system migrations follow the Strangler Fig pattern. Phase 1 (Discovery): document all API endpoints, data flows, and business rules of the legacy system  --  duration 2-4 weeks. Phase 2 (Parallel Build): implement equivalent functionality in the new architecture while the legacy system continues operating  --  duration varies by system size. Phase 3 (Traffic Shifting): gradually route traffic to the new system using feature flags, starting at 5% and increasing by 10% per week. Phase 4 (Decommission): once 100% traffic is on the new system for 30 days with zero critical incidents, the legacy system is archived and infrastructure is deprovisioned."),
            ("5.0 Documentation Debt Standards",
             "All services must maintain up-to-date documentation including: API reference documentation auto-generated from OpenAPI/Swagger specs, architecture decision records (ADRs) for every significant technical decision, runbooks for common operational tasks and incident response, and README files with setup instructions that enable a new developer to run the service locally within 30 minutes. Documentation freshness is audited quarterly  --  services with documentation older than 6 months receive an automatic 'documentation debt' flag on the Tech Health Dashboard. Teams with documentation debt exceeding 3 months are ineligible for production release approval."),
        ]
    },
]


def _add_section(pdf, header, text):
    """Add a formatted section to the current page (spills to next page automatically)."""
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(40, 40, 100)
    pdf.multi_cell(w=pdf.epw, h=10, text=header)
    pdf.ln(3)
    pdf.set_font("helvetica", "", 11)
    pdf.set_text_color(30, 30, 30)
    pdf.multi_cell(w=pdf.epw, h=7, text=text)
    pdf.ln(8)


for doc in DOCUMENTS:
    pdf = PolicyPDF()
    pdf.alias_nb_pages()

    # -- Title page --
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("helvetica", "B", 26)
    pdf.set_text_color(50, 50, 150)
    pdf.multi_cell(w=pdf.epw, h=15, text=doc["title"], align="C")
    pdf.ln(10)
    pdf.set_font("helvetica", "I", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(w=0, h=10, text="Official Executive Publication - 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(20)
    pdf.set_font("helvetica", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(w=pdf.epw, h=8, text=f"This document defines the official {doc['title'].lower()} standards for SGS Technologies. It has been reviewed and approved by the executive leadership team.")

    # -- Content pages --
    for header, text in doc["sections"]:
        pdf.add_page()
        _add_section(pdf, header, text)

    # -- Pad to minimum 5 pages with appendix --
    while pdf.page_no() < 5:
        pdf.add_page()
        pdf.set_font("helvetica", "B", 14)
        pdf.set_text_color(40, 40, 100)
        pdf.multi_cell(w=pdf.epw, h=10, text="Appendix: Revision History")
        pdf.ln(3)
        pdf.set_font("helvetica", "", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(w=pdf.epw, h=7, text="Version 1.0  --  Initial publication. Approved by the Board of Directors.")

    pdf_path = os.path.join(pdf_dir, doc["filename"])
    pdf.output(pdf_path)
    print(f"Generated {doc['filename']} ({pdf.page_no()} pages)")

print("\nAll 10 PDFs generated with UNIQUE content per document.")
