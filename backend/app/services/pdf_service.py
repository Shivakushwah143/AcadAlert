from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Create reports directory if it doesn't exist
REPORTS_DIR = "./reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

async def generate_student_report(student_data: dict, prediction_data: dict, risk_factors: list, suggestions: list) -> str:
    """Generate PDF report for a student"""
    
    try:
        # Create filename
        student_id = student_data.get('student_id', 'unknown')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{student_id}_{timestamp}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4, 
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e3c72'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6
        )
        
        # Title
        title = Paragraph("AcadAlert - Student Risk Assessment Report", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Report Date
        date_text = f"Report Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}"
        story.append(Paragraph(date_text, normal_style))
        story.append(Spacer(1, 20))
        
        # Student Information Section
        story.append(Paragraph("Student Information", heading_style))
        
        # Student info table
        student_info = [
            ["Student ID:", student_data.get('student_id', 'N/A')],
            ["Name:", student_data.get('name', 'N/A')],
            ["Program:", student_data.get('program', 'Not Specified')],
            ["Year/Semester:", student_data.get('year', 'Not Specified')],
        ]
        
        student_table = Table(student_info, colWidths=[150, 300])
        student_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(student_table)
        story.append(Spacer(1, 20))
        
        # Academic Performance Section
        story.append(Paragraph("Academic Performance", heading_style))
        
        performance_data = [
            ["Metric", "Value", "Status"],
            ["Attendance", f"{student_data.get('attendance', 0)}%", 
             "⚠️ Below 75%" if student_data.get('attendance', 100) < 75 else "✅ Good"],
            ["Internal Marks", f"{student_data.get('internal_marks', 0)}/100", 
             "⚠️ Below 60%" if student_data.get('internal_marks', 100) < 60 else "✅ Good"],
            ["Assignment Submission", f"{student_data.get('assignment_submission', 0)}%", 
             "⚠️ Below 70%" if student_data.get('assignment_submission', 100) < 70 else "✅ Good"],
            ["Participation Score", f"{student_data.get('participation_score', 0)}%", 
             "⚠️ Below 60%" if student_data.get('participation_score', 100) < 60 else "✅ Good"],
            ["Backlogs", student_data.get('backlogs', 0), 
             "⚠️ High" if student_data.get('backlogs', 0) > 2 else "✅ Manageable"],
            ["Study Hours", f"{student_data.get('study_hours', 0)} hrs/week", "N/A"],
        ]
        
        perf_table = Table(performance_data, colWidths=[150, 100, 200])
        perf_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(perf_table)
        story.append(Spacer(1, 20))
        
        # Risk Assessment Section
        story.append(Paragraph("Risk Assessment", heading_style))
        
        # Risk level with color coding
        risk_level = prediction_data.get('risk_level', 'UNKNOWN')
        risk_color = {
            'HIGH': colors.HexColor('#e74c3c'),
            'MEDIUM': colors.HexColor('#f39c12'),
            'LOW': colors.HexColor('#27ae60')
        }.get(risk_level, colors.grey)
        
        risk_text = Paragraph(f"<b>Overall Risk Level: {risk_level}</b>", 
                             ParagraphStyle('Risk', parent=normal_style, 
                                          textColor=risk_color, fontSize=14))
        story.append(risk_text)
        story.append(Spacer(1, 10))
        
        risk_score = prediction_data.get('risk_score', 0)
        story.append(Paragraph(f"Risk Score: {risk_score:.2%}", normal_style))
        story.append(Spacer(1, 15))
        
        # Key Risk Factors
        if risk_factors:
            story.append(Paragraph("Key Risk Factors", heading_style))
            for factor in risk_factors:
                factor_text = f"• <b>{factor['factor_name']}</b>: {factor['current_value']}% (Threshold: {factor['threshold']}%) - <font color='red'>High Impact</font>"
                story.append(Paragraph(factor_text, normal_style))
            story.append(Spacer(1, 15))
        
        # Recommendations Section
        story.append(Paragraph("Recommendations & Action Plan", heading_style))
        
        for i, suggestion in enumerate(suggestions, 1):
            story.append(Paragraph(f"{i}. {suggestion}", normal_style))
        
        story.append(Spacer(1, 20))
        
        # Additional Notes
        story.append(Paragraph("Additional Notes", heading_style))
        notes = """
        - This report is generated based on current academic performance data
        - Regular monitoring and timely intervention can improve student outcomes
        - Please consult with academic advisor for detailed guidance
        - Review this report monthly to track progress
        """
        story.append(Paragraph(notes, normal_style))
        story.append(Spacer(1, 20))
        
        # Footer
        footer_text = f"AcadAlert System | Report ID: {filename} | Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(footer_text, 
                              ParagraphStyle('Footer', parent=normal_style, 
                                           fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
        
        # Build PDF
        doc.build(story)
        
        logger.info(f"✅ PDF report generated: {filename}")
        return filepath
        
    except Exception as e:
        logger.error(f"❌ Error generating PDF: {e}")
        raise Exception(f"Failed to generate PDF report: {str(e)}")