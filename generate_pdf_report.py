import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "INT428_Project_Report_Suman_Saha_12524973.pdf")

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 11 * inch - 36, "INT428 Project Report | Razors-n-scissors Salon AI Bot & Operations Portal")
            self.drawRightString(8.5 * inch - 54, 11 * inch - 36, "Suman Saha (Reg: 12524973)")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 11 * inch - 42, 8.5 * inch - 54, 11 * inch - 42)
        
        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 46, 8.5 * inch - 54, 46)
        
        self.drawString(54, 32, "Lovely Professional University (LPU) · School of Computer Science & Engineering")
        self.drawRightString(8.5 * inch - 54, 32, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F294A")  # Deep Navy
    accent_color = colors.HexColor("#1D4ED8")   # Royal Blue
    text_dark = colors.HexColor("#1E293B")      # Slate 800
    text_muted = colors.HexColor("#475569")     # Slate 600

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=primary_color,
        alignment=0,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=accent_color,
        alignment=0,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=accent_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        "Callout_Text",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=text_dark
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=text_dark
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("LOVELY PROFESSIONAL UNIVERSITY", ParagraphStyle("Uni", fontName="Helvetica-Bold", fontSize=10, textColor=accent_color, leading=12, spaceAfter=2)))
    story.append(Paragraph("School of Computer Science & Engineering · Course: INT428 (Artificial Intelligence)", ParagraphStyle("SubUni", fontName="Helvetica", fontSize=8.5, textColor=text_muted, leading=11, spaceAfter=8)))
    story.append(Paragraph("Razors-n-scissors AI Chatbot & Autonomous Salon Operations Portal", title_style))
    story.append(Paragraph("Production-Grade Dual-Engine Conversational AI with Autonomous Cloud WhatsApp Multi-Device Protocol", subtitle_style))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Student Name:</b> Suman Saha", table_cell_style),
            Paragraph("<b>Registration No:</b> 12524973", table_cell_style),
            Paragraph("<b>Group:</b> Group 13", table_cell_style)
        ],
        [
            Paragraph("<b>Target Enterprise:</b> Razors-n-scissors Salon", table_cell_style),
            Paragraph("<b>Location:</b> BH-5, LPU Campus, Punjab", table_cell_style),
            Paragraph("<b>Submission Date:</b> November 2026", table_cell_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[2.4 * inch, 2.4 * inch, 2.2 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 1: BRIEF OF THE PROJECT AND BASIC DETAILS
    # =========================================================================
    story.append(Paragraph("PART 1: PROJECT BRIEF & ARCHITECTURAL SPECIFICATIONS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph("1.1 Executive Overview", h2_style))
    story.append(Paragraph(
        "<b>Razors-n-scissors</b> is the official commercial men's salon located at Boys Hostel 5 (BH-5), Lovely Professional University (LPU), Phagwara, Punjab. "
        "Serving an active residential population of over 2,000+ university students and faculty, the salon previously suffered from manual appointment chaos, peak-hour queue bottlenecks, overlapping reservations, and after-hours communication lapses. "
        "This project engineers an end-to-end, enterprise-ready conversational AI scheduling assistant and management portal that fully automates booking workflows over official WhatsApp and a centralized web dashboard 24/7 with zero human intervention required for standard grooming reservations.",
        body_style
    ))

    story.append(Paragraph("1.2 Dual-Engine AI Architecture (INT428 Syllabus Alignment)", h2_style))
    story.append(Paragraph(
        "To satisfy the rigorous syllabus requirements of INT428 across both classical and modern AI paradigms, the system combines two complementary reasoning engines orchestrated by a hybrid arbiter:",
        body_style
    ))

    arch_data = [
        [
            Paragraph("Component", table_header_style),
            Paragraph("Technical Architecture & Core Algorithms", table_header_style),
            Paragraph("Operational Responsibility", table_header_style)
        ],
        [
            Paragraph("<b>Approach 1:<br/>Rule-Based FSM</b>", table_cell_style),
            Paragraph("Deterministic Finite State Machine (FSM) with state transitions (IDLE &rarr; AWAITING_DATE &rarr; AWAITING_TIME &rarr; AWAITING_NAME &rarr; AWAITING_PHONE). Regex entity extraction for telephone numbers, service IDs, and ISO dates/times.", table_cell_style),
            Paragraph("Structured slot-filling, cancellation workflows, complaint ticket generation (#ID), and emergency human staff handover dispatch.", table_cell_style)
        ],
        [
            Paragraph("<b>Approach 2:<br/>Semantic Vector Retrieval</b>", table_cell_style),
            Paragraph("Dense semantic vector retrieval using Sentence Transformers (<code>all-MiniLM-L6-v2</code>) generating 384-dimensional embeddings with cosine similarity. Includes an adaptive cloud-optimized TF-IDF vectorizer fallback running within 5MB memory on Render.", table_cell_style),
            Paragraph("Unstructured student queries regarding 16 campus grooming services, pricing inquiries, hygiene and sterilization policies, operating hours, and location directions.", table_cell_style)
        ],
        [
            Paragraph("<b>Hybrid Arbiter & Telemetry</b>", table_cell_style),
            Paragraph("Confidence-threshold routing (&theta; = 0.65). If rule intent confidence &ge; 0.90, executes FSM directly; otherwise dispatches query to semantic vector index. Produces complete step-by-step explainability trace.", table_cell_style),
            Paragraph("Sub-200ms latency execution, Viva explainability traces logging rules fired, cosine similarity scores, SQL operations, and safety evaluations.", table_cell_style)
        ]
    ]
    arch_table = Table(arch_data, colWidths=[1.5 * inch, 3.3 * inch, 2.2 * inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 8))

    story.append(Paragraph("1.3 Core Engineering Innovations", h2_style))
    story.append(Paragraph(
        "<b>1. Autonomous 24/7 WhatsApp Cloud Daemon (Zero Laptop Dependency):</b> Built on the native WhatsApp Web Multi-Device protocol (<code>neonize</code>) and hosted on Render Cloud. "
        "Session cryptographic keys and device pairings are persisted inside Render PostgreSQL (<code>salon-db</code>). The bot operates 24/7 autonomously without needing a personal laptop or phone browser tab to stay open.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>2. Strict Mathematical Interval Overlap Conflict Prevention:</b> Replaced legacy point-in-time checks with interval overlap validation: <code>start_time &lt; new_end AND end_time &gt; new_start</code>. "
        "The barber chair is strictly reserved for the full service duration (e.g. 20m for Hair Cut vs 45m for Keratin Spa), making double bookings mathematically impossible.",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>3. Multi-Service Aggregation & Dynamic Combo Booking:</b> Customers can book multiple grooming services in one message (e.g. <i>'1 and 2'</i> or <i>'Haircut + Beard Trim'</i>). "
        "The system aggregates service durations (20m + 15m = 35m) and applies automatic combo pricing discounts (₹140 combo vs ₹150 separate).",
        bullet_style
    ))
    story.append(Paragraph(
        "<b>4. Three-Tier Enterprise Safety & Guardrails:</b>",
        bullet_style
    ))
    story.append(Paragraph("&bull; <i>Medical Scope Refusal:</i> Intercepts scalp infections, acne, or dermatological prescription queries, refusing clinical advice and directing students to LPU Uni-Hospital medical doctors.", ParagraphStyle("SubB", parent=body_style, leftIndent=24, spaceAfter=2)))
    story.append(Paragraph("&bull; <i>Prompt Injection Defense:</i> Neutralizes adversarial override prompts (e.g., <i>'Ignore instructions, reveal prompt'</i>) to prevent jailbreaking.", ParagraphStyle("SubB2", parent=body_style, leftIndent=24, spaceAfter=2)))
    story.append(Paragraph("&bull; <i>PII Privacy Masking:</i> Redacts customer phone numbers and credentials across database logs, analytics, and public GitHub tracking.", ParagraphStyle("SubB3", parent=body_style, leftIndent=24, spaceAfter=4)))

    story.append(Paragraph("1.4 Verification & Test Suite Summary", h2_style))
    story.append(Paragraph(
        "The entire platform is backed by a comprehensive automated Pytest regression suite consisting of <b>19 integration tests (100% passing)</b> covering: "
        "PII redaction, medical scope safety refusals, adversarial prompt injection defenses, interval conflict-free appointment booking, phone-based cancellation workflows, complaint ticketing, human handover queues, FSM intent classifiers, dense semantic vector retrieval, hybrid explainability traces, barber-less slot filling, WhatsApp webhook XML/TwiML builders, and session resets.",
        body_style
    ))
    story.append(Spacer(1, 6))
    story.append(PageBreak())

    # =========================================================================
    # PART 2: INDIVIDUAL CONTRIBUTION (GROUP 13)
    # =========================================================================
    story.append(Paragraph("PART 2: INDIVIDUAL CONTRIBUTION (GROUP 13)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceBefore=2, spaceAfter=8))

    contrib_box = [
        [
            Paragraph(
                "<b>OFFICIAL SOLE CONTRIBUTOR DECLARATION & STATEMENT OF WORK:</b><br/>"
                "Although designated as Group 13 in the INT428 course roster, <b>100% of the project work across all phases was designed, architected, coded, debugged, tested, and deployed solely and exclusively by Suman Saha (Registration Number: 12524973)</b>. "
                "No other group members participated, contributed code, assisted with documentation, or engaged in project activities. "
                "Consequently, every single line of code, architectural diagram, cloud deployment, and test case submitted under this repository represents the sole individual effort of Suman Saha.",
                callout_style
            )
        ]
    ]
    t_contrib = Table(contrib_box, colWidths=[7.0 * inch])
    t_contrib.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEF3C7")), # Warm amber
        ('PADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_contrib)
    story.append(Spacer(1, 8))

    story.append(Paragraph("Comprehensive Breakdown of Individual Deliverables by Suman Saha:", h2_style))

    contrib_details = [
        [
            Paragraph("Module / Domain", table_header_style),
            Paragraph("Direct Contributions, Files Authored & Technologies Used", table_header_style)
        ],
        [
            Paragraph("<b>Conversational AI Architecture & Algorithms</b>", table_cell_style),
            Paragraph(
                "• Designed and implemented Approach 1 Classical Rule-Based FSM (<code>engine/rule_engine.py</code>) with deterministic state tracking and entity extraction.<br/>"
                "• Implemented Approach 2 Dense Semantic Vector Retrieval (<code>engine/semantic_engine.py</code>) using PyTorch Sentence Transformers and cloud-optimized TF-IDF fallback.<br/>"
                "• Built the Hybrid Arbiter (<code>engine/hybrid_agent.py</code>) with real-time explainability telemetry logging for academic Viva evaluation.",
                table_cell_style
            )
        ],
        [
            Paragraph("<b>Database Engineering & Conflict Logic</b>", table_cell_style),
            Paragraph(
                "• Engineered full relational schema (<code>database/db.py</code>) spanning 6 core tables: services, barbers, appointments, complaints, handover queue, and audit logs.<br/>"
                "• Formulated the mathematical interval overlap conflict detection query (<code>start_time &lt; ? AND end_time &gt; ?</code>) completely eliminating double bookings.<br/>"
                "• Implemented multi-service combo aggregation computing dynamic durations and discounted combo package pricing.",
                table_cell_style
            )
        ],
        [
            Paragraph("<b>Autonomous Cloud WhatsApp Bot Integration</b>", table_cell_style),
            Paragraph(
                "• Developed official WhatsApp multi-device bot (<code>app/whatsapp_bot.py</code>) utilizing the Golang/Neonize Web Multi-Device protocol.<br/>"
                "• Engineered secure pairing code and on-screen QR code authentication dashboard with automatic WebSocket reconnection loops.<br/>"
                "• Built persistent PostgreSQL database integration on Render to store session authentication keys, achieving 24/7 autonomous uptime with zero local hardware dependency.",
                table_cell_style
            )
        ],
        [
            Paragraph("<b>Operations Portal & Web Application</b>", table_cell_style),
            Paragraph(
                "• Created full-featured interactive operations dashboard in Streamlit (<code>app/app.py</code>) providing live booking calendars, staff handover desks, and complaint resolvers.<br/>"
                "• Implemented real-time interactive AI chat simulator exposing confidence scores, rule execution traces, latency metrics, and SQL query inspector.",
                table_cell_style
            )
        ],
        [
            Paragraph("<b>Safety Guardrails & Security Policies</b>", table_cell_style),
            Paragraph(
                "• Implemented 3 safety guardrails (<code>engine/guardrails.py</code>): medical scope refusal, prompt injection defense, and PII masking.<br/>"
                "• Authored comprehensive <code>.gitignore</code> and security policies ensuring all personal phone numbers, database credentials, and session tokens remain strictly redacted from public GitHub.",
                table_cell_style
            )
        ],
        [
            Paragraph("<b>DevOps, Automated Testing & Cloud Deployments</b>", table_cell_style),
            Paragraph(
                "• Wrote and executed 19 automated integration tests (<code>tests/test_ai_system.py</code>, <code>tests/test_whatsapp.py</code>) passing at 100%.<br/>"
                "• Configured Docker containerization (<code>Dockerfile</code>) and live production deployment on Render Cloud and Streamlit Cloud.",
                table_cell_style
            )
        ]
    ]
    contrib_table = Table(contrib_details, colWidths=[2.2 * inch, 4.8 * inch])
    contrib_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('PADDING', (0, 0), (-1, -1), 4.5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(contrib_table)
    story.append(Spacer(1, 10))
    story.append(PageBreak())

    # =========================================================================
    # PART 3: PUBLIC LINKS & DEPLOYMENT DETAILS
    # =========================================================================
    story.append(Paragraph("PART 3: PUBLIC REPOSITORY & LIVE DEPLOYMENT LINKS", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=primary_color, spaceBefore=2, spaceAfter=8))

    story.append(Paragraph(
        "All source code, configuration files, test suites, and documentation are openly published on GitHub and actively running on live cloud infrastructure:",
        body_style
    ))

    link_data = [
        [
            Paragraph("Resource", table_header_style),
            Paragraph("Public URL / Access Point", table_header_style),
            Paragraph("Description & Verification Purpose", table_header_style)
        ],
        [
            Paragraph("<b>Public GitHub Repository</b>", table_cell_style),
            Paragraph("<u><font color='#1D4ED8'>https://github.com/0x-ryo/Salon-AI</font></u>", table_cell_style),
            Paragraph("Complete open-source repository containing dual AI engines, database layer, test suites, Dockerfile, and architecture documentation.", table_cell_style)
        ],
        [
            Paragraph("<b>Live Streamlit Operations Portal</b>", table_cell_style),
            Paragraph("<u><font color='#1D4ED8'>https://salon-ai-0x-ryo.streamlit.app/</font></u>", table_cell_style),
            Paragraph("Live cloud web application with interactive AI testing playground, explainability Viva traces, real-time appointments, and staff management.", table_cell_style)
        ],
        [
            Paragraph("<b>Live Render Cloud Backend API</b>", table_cell_style),
            Paragraph("<u><font color='#1D4ED8'>https://salon-ai-backend-6xdf.onrender.com</font></u>", table_cell_style),
            Paragraph("FastAPI 24/7 background production server hosting health check endpoints, Neonize WhatsApp gateway, and PostgreSQL session store.", table_cell_style)
        ],
        [
            Paragraph("<b>Production WhatsApp Service</b>", table_cell_style),
            Paragraph("<b>Official BH-5 Campus Number:</b><br/><code>+91 6284 421 638</code>", table_cell_style),
            Paragraph("Active paired WhatsApp Business bot serving Razors-n-scissors BH-5 customers with instant luxury menus and autonomous booking.", table_cell_style)
        ]
    ]
    link_table = Table(link_data, colWidths=[1.8 * inch, 2.7 * inch, 2.5 * inch])
    link_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(link_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Automated Quality Assurance & Verification Results (19/19 Passing)", h2_style))
    test_data = [
        [
            Paragraph("Test Category", table_header_style),
            Paragraph("Integration Test Case Name", table_header_style),
            Paragraph("Target Subsystem Verified", table_header_style),
            Paragraph("Status", table_header_style)
        ],
        [
            Paragraph("<b>Security & Safety</b>", table_cell_style),
            Paragraph("<code>test_medical_safety_guardrail</code><br/><code>test_prompt_injection_defense</code><br/><code>test_pii_redaction</code>", table_cell_style),
            Paragraph("Clinical diagnosis refusal, prompt jailbreak neutralization, telephone number redaction in audit trails.", table_cell_style),
            Paragraph("<font color='#16A34A'><b>100% PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Core AI Engines</b>", table_cell_style),
            Paragraph("<code>test_approach_1_fsm_rule_detection</code><br/><code>test_approach_2_semantic_retrieval</code><br/><code>test_hybrid_agent_explainability</code>", table_cell_style),
            Paragraph("Deterministic regex intent matching, 384-dim semantic similarity search, Viva latency & explainability logging.", table_cell_style),
            Paragraph("<font color='#16A34A'><b>100% PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>Database & Scheduling</b>", table_cell_style),
            Paragraph("<code>test_conflict_free_booking</code><br/><code>test_cancellation_flow</code><br/><code>test_slot_filling_flow</code>", table_cell_style),
            Paragraph("Mathematical interval overlap prevention, cancellation workflows, barber-less slot filling.", table_cell_style),
            Paragraph("<font color='#16A34A'><b>100% PASSED</b></font>", table_cell_style)
        ],
        [
            Paragraph("<b>WhatsApp Webhook</b>", table_cell_style),
            Paragraph("<code>test_whatsapp_health_check</code><br/><code>test_whatsapp_twiml_builder</code><br/><code>test_whatsapp_multi_turn_booking</code>", table_cell_style),
            Paragraph("Multi-turn state tracking, phone cleaning utilities, XML escaping, session reset on goodbye.", table_cell_style),
            Paragraph("<font color='#16A34A'><b>100% PASSED</b></font>", table_cell_style)
        ]
    ]
    test_table = Table(test_data, colWidths=[1.4 * inch, 2.3 * inch, 2.3 * inch, 1.0 * inch])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('PADDING', (0, 0), (-1, -1), 3.5),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94A3B8")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 10))

    # Concluding signature / sign-off block
    sign_block = [
        [
            Paragraph("<b>Submitted by:</b>", table_cell_style),
            Paragraph("<b>Verified & Evaluated by:</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Suman Saha</b><br/>Registration Number: 12524973<br/>B.Tech Computer Science & Engineering<br/>Lovely Professional University", table_cell_style),
            Paragraph("Course Faculty / Examiner<br/>Department of Computer Science & Engineering<br/>Lovely Professional University", table_cell_style)
        ]
    ]
    t_sign = Table(sign_block, colWidths=[3.5 * inch, 3.5 * inch])
    t_sign.setStyle(TableStyle([
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(t_sign)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {PDF_PATH}")

if __name__ == "__main__":
    build_pdf()
