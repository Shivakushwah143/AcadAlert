from datetime import datetime
import logging
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

logger = logging.getLogger(__name__)

REPORTS_DIR = "./reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


async def generate_student_report(
    student_data: dict, prediction_data: dict, risk_factors: list, suggestions: list
) -> str:
    """Generate PDF report for a student"""
    try:
        student_id = student_data.get("student_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{student_id}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#1e3c72"),
            spaceAfter=30,
            alignment=TA_CENTER,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
            spaceBefore=20,
        )

        normal_style = ParagraphStyle(
            "CustomNormal", parent=styles["Normal"], fontSize=10, spaceAfter=6
        )

        title = Paragraph("AcadAlert - Student Risk Assessment Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        date_text = f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        story.append(Paragraph(date_text, normal_style))
        story.append(Spacer(1, 20))

        story.append(Paragraph("Student Information", heading_style))

        student_info = [
            ["Student ID:", student_data.get("student_id", "N/A")],
            ["Name:", student_data.get("student_name", "N/A")],
            ["Semester:", student_data.get("semester", "N/A")],
        ]

        student_table = Table(student_info, colWidths=[150, 300])
        student_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(student_table)
        story.append(Spacer(1, 20))

        story.append(Paragraph("Academic Performance", heading_style))

        attendance_value = student_data.get("attendance_percentage", 0)
        internal_marks_value = student_data.get("internal_marks", 0)
        assignment_value = student_data.get("assignment_submission_rate", 0)

        performance_data = [
            ["Metric", "Value", "Status"],
            [
                "Attendance",
                f"{attendance_value}%",
                "Below 75%" if attendance_value < 75 else "Good",
            ],
            [
                "Internal Marks",
                f"{internal_marks_value}/100",
                "Below 60%" if internal_marks_value < 60 else "Good",
            ],
            [
                "Assignment Submission",
                f"{assignment_value}%",
                "Below 70%" if assignment_value < 70 else "Good",
            ],
            ["Semester", str(student_data.get("semester", "N/A")), ""],
        ]

        perf_table = Table(performance_data, colWidths=[170, 110, 170])
        perf_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(perf_table)
        story.append(Spacer(1, 20))

        story.append(Paragraph("Risk Assessment", heading_style))

        risk_level = prediction_data.get("risk_level", "UNKNOWN")
        risk_color = {
            "HIGH": colors.HexColor("#e74c3c"),
            "MEDIUM": colors.HexColor("#f39c12"),
            "LOW": colors.HexColor("#27ae60"),
        }.get(risk_level, colors.grey)

        risk_text = Paragraph(
            f"<b>Overall Risk Level: {risk_level}</b>",
            ParagraphStyle(
                "Risk", parent=normal_style, textColor=risk_color, fontSize=14
            ),
        )
        story.append(risk_text)
        story.append(Spacer(1, 10))

        risk_score = prediction_data.get("risk_score", 0)
        if isinstance(risk_score, (int, float)) and risk_score <= 1:
            risk_score_text = f"Risk Score: {risk_score:.2%}"
        else:
            risk_score_text = f"Risk Score: {risk_score}"
        story.append(Paragraph(risk_score_text, normal_style))
        story.append(Spacer(1, 15))

        if risk_factors:
            story.append(Paragraph("Key Risk Factors", heading_style))
            for factor in risk_factors:
                factor_text = (
                    f"- {factor['factor_name']}: {factor['current_value']} "
                    f"(Threshold: {factor['threshold']})"
                )
                story.append(Paragraph(factor_text, normal_style))
            story.append(Spacer(1, 15))

        story.append(Paragraph("Recommendations & Action Plan", heading_style))
        for i, suggestion in enumerate(suggestions, 1):
            story.append(Paragraph(f"{i}. {suggestion}", normal_style))

        story.append(Spacer(1, 20))

        story.append(Paragraph("Additional Notes", heading_style))
        notes = (
            "- This report is generated based on current academic performance data."
            "<br/>- Regular monitoring and timely intervention can improve outcomes."
            "<br/>- Please consult an academic advisor for detailed guidance."
            "<br/>- Review this report monthly to track progress."
        )
        story.append(Paragraph(notes, normal_style))
        story.append(Spacer(1, 20))

        footer_text = (
            "AcadAlert System | "
            f"Report ID: {filename} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        story.append(
            Paragraph(
                footer_text,
                ParagraphStyle(
                    "Footer",
                    parent=normal_style,
                    fontSize=8,
                    textColor=colors.grey,
                    alignment=TA_CENTER,
                ),
            )
        )

        doc.build(story)

        logger.info("PDF report generated: %s", filename)
        return filepath

    except Exception as exc:
        logger.error("Error generating PDF: %s", exc)
        raise Exception(f"Failed to generate PDF report: {str(exc)}")
