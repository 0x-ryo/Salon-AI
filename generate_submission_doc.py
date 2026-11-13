import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_FILENAME = "INT428_Group13_Suman_Saha_12524973_Submission.pdf"

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
            self.draw_footer(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 18, "INT428 Capstone Project Submission · Group 13 · Suman Saha (Reg. 12524973)")
        self.drawRightString(A4[0] - 36, 18, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    # A4 dimensions: 595.27 x 841.89 points
    # Printable height: ~780 points with margins
    doc = SimpleDocTemplate(
        PDF_FILENAME,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=26,
        bottomMargin=26
    )

    primary_color = colors.HexColor("#0f172a")   # Dark Navy
    accent_color = colors.HexColor("#1d4ed8")    # Royal Blue
    dark_text = colors.HexColor("#1e293b")
    muted_text = colors.HexColor("#475569")
    border_color = colors.HexColor("#cbd5e1")
    bg_light = colors.HexColor("#f8fafc")

    title_style = ParagraphStyle(
        "DocTitle",
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        textColor=primary_color,
        alignment=1
    )

    sub_title_style = ParagraphStyle(
        "DocSubTitle",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=accent_color,
        alignment=1
    )

    sec_heading = ParagraphStyle(
        "SecHeading",
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        textColor=primary_color,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        "Body",
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.2,
        textColor=dark_text
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=11.2,
        textColor=dark_text
    )

    elements = []

    # Institution & Document Header
    elements.append(Paragraph("LOVELY PROFESSIONAL UNIVERSITY", ParagraphStyle("Univ", fontName="Helvetica-Bold", fontSize=9, leading=11, alignment=1, textColor=muted_text)))
    elements.append(Paragraph("DEPARTMENT OF COMPUTER SCIENCE & ENGINEERING", ParagraphStyle("Dept", fontName="Helvetica", fontSize=7.5, leading=9.5, alignment=1, textColor=muted_text)))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph("INT428: ARTIFICIAL INTELLIGENCE FOUNDATIONS", title_style))
    elements.append(Spacer(1, 1))
    elements.append(Paragraph("CAPSTONE PROJECT OFFICIAL SUBMISSION DOCUMENT", sub_title_style))
    elements.append(Spacer(1, 4))

    elements.append(HRFlowable(width="100%", thickness=1.2, color=accent_color, spaceBefore=0, spaceAfter=5))

    # Basic Details Table
    details_data = [
        [
            Paragraph("<b>Course Code & Title:</b> INT428: Artificial Intelligence Foundations", body_style),
            Paragraph("<b>Group Number:</b> Group 13", body_style)
        ],
        [
            Paragraph("<b>Official Allocated Topic:</b> Customer Support Chatbot & Operational Management Portal for a Real Small Business", body_style),
            Paragraph("<b>Candidate Name:</b> Suman Saha", body_style)
        ],
        [
            Paragraph("<b>Target Enterprise / Location:</b> Razors-n-scissors (BH-5, LPU Campus)", body_style),
            Paragraph("<b>Registration Number:</b> 12524973", body_style)
        ]
    ]

    t_details = Table(details_data, colWidths=[340, 183])
    t_details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg_light),
        ("BOX", (0, 0), (-1, -1), 0.75, border_color),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, border_color),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_details)
    elements.append(Spacer(1, 6))

    # PART 1: Project Brief & Basic Details
    elements.append(Paragraph("PART 1: PROJECT BRIEF & BASIC DETAILS", sec_heading))
    elements.append(Paragraph(
        "<b>Official Allocated Title:</b> <i>Customer Support Chatbot & Operational Management Portal for a Real Small Business</i>",
        body_style
    ))
    elements.append(Spacer(1, 2))
    brief_text = (
        "This project implements an autonomous conversational AI assistant and real-time operations management system "
        "custom-built for <b>Razors-n-scissors</b> (BH-5 Boys Hostel, Lovely Professional University Campus). The solution eliminates front-desk "
        "telephone interruptions and prevents missed after-hours reservations by automating 24/7 appointment scheduling, service inquiries, "
        "grievance registration, and escalation queues directly over official WhatsApp without human staff intervention.<br/><br/>"
        "<b>Key Technical Specifications & Syllabus Implementations:</b><br/>"
        "• <b>Dual AI Engine (INT428 Syllabus Requirement):</b> Implemented and benchmarked <i>Approach 1 (Deterministic Rule-Based FSM Slot-Filler)</i> "
        "against <i>Approach 2 (Dense Sentence-Transformers Semantic Retrieval)</i>, unified via a production Hybrid Arbiter with live explainability traces.<br/>"
        "• <b>Multi-Turn Appointment Scheduling:</b> Direct one-click service selection, multi-service combo support (e.g., Hair Cut + Beard Trim with "
        "automatic duration aggregation and package discount), and live date/time slot filling.<br/>"
        "• <b>Strict Interval Overlap Prevention:</b> Mathematical chair conflict prevention ensuring no two clients are booked simultaneously on the same seat "
        "using interval intersection logic (<i>start₁ &lt; end₂ ∧ end₁ &gt; start₂</i>).<br/>"
        "• <b>24/7 Cloud Architecture (Zero Laptop Dependency):</b> Deployed on Render Cloud with persistent PostgreSQL database preserving multi-device "
        "session keys permanently across restarts, synced in real-time with a Streamlit Cloud operations dashboard.<br/>"
        "• <b>Responsible AI Guardrails:</b> Automated DPDP Act PII masking in audit logs and clinical boundary guardrails refusing medical scalp advice."
    )
    elements.append(Paragraph(brief_text, body_style))
    elements.append(Spacer(1, 6))

    # PART 2: Individual Contribution (Group 13)
    elements.append(Paragraph("PART 2: INDIVIDUAL CONTRIBUTION (GROUP 13)", sec_heading))
    contrib_text = (
        "<b>Statement of 100% Sole Individual Authorship:</b><br/>"
        "Although Group 13 was officially allocated with three roster slots on university records, the entire capstone project was "
        "<b>solely conceptualized, architected, coded, benchmarked, tested, and deployed individually by Suman Saha (Registration No: 12524973)</b>.<br/><br/>"
        "The other two allocated group members did not communicate, coordinate, write code, contribute documentation, or participate in any phase of "
        "this project. Every technical artifact—including the dual AI models, relational database schemas, real WhatsApp WebSocket gateway, "
        "Streamlit live counter dashboard, automated 19-test test suite, and cloud hosting infrastructure—was executed solely by Suman Saha."
    )

    t_contrib = Table([[Paragraph(contrib_text, body_style)]], colWidths=[523])
    t_contrib.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef2f2")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#f87171")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(t_contrib)
    elements.append(Spacer(1, 6))

    # PART 3: Public GitHub Repository
    elements.append(Paragraph("PART 3: PUBLIC GITHUB REPOSITORY LINK", sec_heading))
    elements.append(Paragraph(
        "In accordance with official submission requirements, the complete open-source repository containing source code, test suites, architecture schemas, and deployment scripts is available at the link below:",
        body_style
    ))
    elements.append(Spacer(1, 3))

    link_data = [[
        Paragraph("<b>Public GitHub Repository Link:</b> &nbsp; <font color=\"#1d4ed8\"><u>https://github.com/0x-ryo/Chatbot</u></font>", body_bold)
    ]]
    t_link = Table(link_data, colWidths=[523])
    t_link.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eff6ff")),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#60a5fa")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_link)

    doc.build(elements, canvasmaker=NumberedCanvas)

    with open(PDF_FILENAME, "rb") as f:
        data = f.read()
    pages = re.findall(rb"/Type\s*/Page\b", data)
    print(f"SUCCESS: Generated {PDF_FILENAME}")
    print(f"Verified Page Count: {len(pages)}")

if __name__ == "__main__":
    build_pdf()
