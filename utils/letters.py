"""
Letter generation for compliance notices
Generates PDF letters for water systems with violations
"""

from typing import Dict, Any, List
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

class ComplianceLetterGenerator:
    """Generate compliance letters for water systems"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f4788'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='Warning',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#dc3545'),
            bold=True,
            spaceAfter=12
        ))
    
    def generate_violation_notice(self, system_data: Dict[str, Any], violations: List[Dict[str, Any]]) -> bytes:
        """Generate a violation notice letter"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1*inch)
        story = []
        
        # Header
        story.append(Paragraph("GEORGIA ENVIRONMENTAL PROTECTION DIVISION", self.styles['CustomTitle']))
        story.append(Paragraph("NOTICE OF VIOLATION", self.styles['Title']))
        story.append(Spacer(1, 0.25*inch))
        
        # Date
        story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", self.styles['Normal']))
        story.append(Spacer(1, 0.25*inch))
        
        # System Information
        system = system_data.get('system', {})
        story.append(Paragraph(f"<b>Water System:</b> {system.get('PWS_NAME', 'Unknown')}", self.styles['CustomBody']))
        story.append(Paragraph(f"<b>PWSID:</b> {system.get('PWSID', 'Unknown')}", self.styles['CustomBody']))
        story.append(Paragraph(f"<b>Address:</b> {system.get('CITY_NAME', '')}, {system.get('STATE_CODE', 'GA')} {system.get('ZIP_CODE', '')}", self.styles['CustomBody']))
        story.append(Paragraph(f"<b>Population Served:</b> {system.get('POPULATION_SERVED_COUNT', 0):,}", self.styles['CustomBody']))
        story.append(Spacer(1, 0.25*inch))
        
        # Violation Summary
        story.append(Paragraph("VIOLATION SUMMARY", self.styles['Heading2']))
        story.append(Paragraph(
            f"Your water system has {len(violations)} violation(s) that require immediate attention:",
            self.styles['Warning']
        ))
        story.append(Spacer(1, 0.1*inch))
        
        # Violations Table
        violation_data = [['Violation Type', 'Date', 'Status', 'Health Risk']]
        for v in violations[:10]:  # Limit to 10 most recent
            violation_data.append([
                v.get('VIOLATION_DESC', 'Unknown')[:40] + '...' if len(v.get('VIOLATION_DESC', '')) > 40 else v.get('VIOLATION_DESC', 'Unknown'),
                v.get('NON_COMPL_PER_BEGIN_DATE', '')[:10],
                v.get('VIOLATION_STATUS', 'Unknown'),
                'Yes' if v.get('IS_HEALTH_BASED_IND') == 'Y' else 'No'
            ])
        
        table = Table(violation_data, colWidths=[3*inch, 1.2*inch, 1.2*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 0.25*inch))
        
        # Required Actions
        story.append(Paragraph("REQUIRED ACTIONS", self.styles['Heading2']))
        story.append(Paragraph(
            "You must take the following actions to return to compliance:",
            self.styles['CustomBody']
        ))
        
        actions = [
            "1. Review all violations listed above and determine root causes",
            "2. Submit a corrective action plan within 30 days",
            "3. Implement corrective measures immediately for health-based violations",
            "4. Provide public notification if required by regulations",
            "5. Submit compliance documentation when violations are resolved"
        ]
        
        for action in actions:
            story.append(Paragraph(action, self.styles['CustomBody']))
        
        story.append(Spacer(1, 0.25*inch))
        
        # Contact Information
        story.append(Paragraph("CONTACT INFORMATION", self.styles['Heading2']))
        story.append(Paragraph(
            "For questions or to submit documentation, please contact:",
            self.styles['CustomBody']
        ))
        story.append(Paragraph("Georgia EPD Drinking Water Program", self.styles['CustomBody']))
        story.append(Paragraph("Phone: (404) 656-4713", self.styles['CustomBody']))
        story.append(Paragraph("Email: EPDComments@dnr.ga.gov", self.styles['CustomBody']))
        
        story.append(Spacer(1, 0.5*inch))
        
        # Footer
        story.append(Paragraph(
            "Failure to comply with this notice may result in enforcement action including fines and penalties.",
            self.styles['Warning']
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_compliance_certificate(self, system_data: Dict[str, Any]) -> bytes:
        """Generate a certificate of compliance for systems with no violations"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=1.5*inch)
        story = []
        
        # Header with border
        story.append(Paragraph("CERTIFICATE OF COMPLIANCE", self.styles['Title']))
        story.append(Paragraph("Georgia Environmental Protection Division", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Certificate Body
        system = system_data.get('system', {})
        story.append(Paragraph("This certifies that", self.styles['CustomBody']))
        story.append(Spacer(1, 0.1*inch))
        
        story.append(Paragraph(f"<b>{system.get('PWS_NAME', 'Unknown')}</b>", self.styles['Title']))
        story.append(Paragraph(f"PWSID: {system.get('PWSID', 'Unknown')}", self.styles['Normal']))
        story.append(Spacer(1, 0.25*inch))
        
        story.append(Paragraph(
            "is currently in compliance with all applicable drinking water regulations "
            "under the Safe Drinking Water Act as administered by the State of Georgia.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 0.5*inch))
        
        # System Details
        details = [
            ['System Type:', system.get('PWS_TYPE_CODE', 'Unknown')],
            ['Population Served:', f"{system.get('POPULATION_SERVED_COUNT', 0):,}"],
            ['Certificate Date:', datetime.now().strftime('%B %d, %Y')],
            ['Valid Until:', datetime(datetime.now().year + 1, datetime.now().month, datetime.now().day).strftime('%B %d, %Y')]
        ]
        
        detail_table = Table(details, colWidths=[2*inch, 4*inch])
        detail_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12)
        ]))
        story.append(detail_table)
        story.append(Spacer(1, 1*inch))
        
        # Signature line
        story.append(Paragraph("_" * 40, self.styles['Normal']))
        story.append(Paragraph("Authorized Signature", self.styles['Normal']))
        story.append(Paragraph("Georgia EPD Drinking Water Program", self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_public_notice(self, system_data: Dict[str, Any], violation: Dict[str, Any]) -> bytes:
        """Generate public notification template for health-based violations"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch)
        story = []
        
        # Header
        story.append(Paragraph("IMPORTANT INFORMATION ABOUT YOUR DRINKING WATER", self.styles['Title']))
        story.append(Spacer(1, 0.25*inch))
        
        # System Info
        system = system_data.get('system', {})
        story.append(Paragraph(f"<b>{system.get('PWS_NAME', 'Unknown')} Has Levels of {violation.get('VIOLATION_DESC', 'Contaminants')} Above Drinking Water Standards</b>", self.styles['Warning']))
        story.append(Spacer(1, 0.25*inch))
        
        # What happened
        story.append(Paragraph("<b>What Happened?</b>", self.styles['Heading2']))
        story.append(Paragraph(
            f"Our water system recently violated a drinking water standard. Although this is not an emergency, "
            f"as our customers, you have a right to know what happened, what you should do, and what we are doing to correct this situation.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Details
        story.append(Paragraph(
            f"We routinely monitor for drinking water contaminants. Testing on {violation.get('NON_COMPL_PER_BEGIN_DATE', 'N/A')} "
            f"showed {violation.get('VIOLATION_DESC', 'contamination')} levels that exceed the standard.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # What should I do
        story.append(Paragraph("<b>What Should I Do?</b>", self.styles['Heading2']))
        
        # Check if it's a health-based violation
        if violation.get('IS_HEALTH_BASED_IND') == 'Y':
            story.append(Paragraph(
                "• If you have specific health concerns, consult your doctor",
                self.styles['CustomBody']
            ))
            story.append(Paragraph(
                "• Consider using bottled water for drinking and cooking until the issue is resolved",
                self.styles['CustomBody']
            ))
            story.append(Paragraph(
                "• People with severely compromised immune systems, infants, and some elderly may be at increased risk",
                self.styles['CustomBody']
            ))
        else:
            story.append(Paragraph(
                "• This is not an immediate health risk",
                self.styles['CustomBody']
            ))
            story.append(Paragraph(
                "• You do not need to use alternative water supplies",
                self.styles['CustomBody']
            ))
        
        story.append(Spacer(1, 0.2*inch))
        
        # What is being done
        story.append(Paragraph("<b>What Is Being Done?</b>", self.styles['Heading2']))
        story.append(Paragraph(
            f"We are working with the Georgia EPD to resolve this issue. Steps being taken include:",
            self.styles['CustomBody']
        ))
        story.append(Paragraph("• Investigating the source of contamination", self.styles['CustomBody']))
        story.append(Paragraph("• Implementing corrective actions", self.styles['CustomBody']))
        story.append(Paragraph("• Increasing monitoring frequency", self.styles['CustomBody']))
        story.append(Paragraph("• We anticipate resolving the problem within 90 days", self.styles['CustomBody']))
        story.append(Spacer(1, 0.2*inch))
        
        # Contact info
        story.append(Paragraph("<b>For More Information:</b>", self.styles['Heading2']))
        story.append(Paragraph(f"Contact: {system.get('PWS_NAME', 'Water System')}", self.styles['CustomBody']))
        story.append(Paragraph(f"Phone: {system.get('PHONE_NUMBER', '(XXX) XXX-XXXX')}", self.styles['CustomBody']))
        story.append(Paragraph(f"PWSID: {system.get('PWSID', 'Unknown')}", self.styles['CustomBody']))
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Paragraph(
            f"Please share this information with all the other people who drink this water, especially those who may not have received this notice directly.",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"Date distributed: {datetime.now().strftime('%B %d, %Y')}",
            self.styles['Normal']
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()