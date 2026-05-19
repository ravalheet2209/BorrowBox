import os
import sys
import django

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO

def get_pdf_styles():
    styles = getSampleStyleSheet()
    primary_color = colors.HexColor('#6d28d9')
    text_color = colors.HexColor('#0d0d12')

    styles.add(ParagraphStyle(name='CustomTitle', parent=styles['Heading1'],
                              fontName='Helvetica-Bold', fontSize=22,
                              textColor=primary_color, spaceAfter=20, alignment=1))
    styles.add(ParagraphStyle(name='Subtitle', parent=styles['Heading2'],
                              fontName='Helvetica-Bold', fontSize=14,
                              textColor=colors.gray, spaceAfter=20, alignment=1))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading3'],
                              fontName='Helvetica-Bold', fontSize=14,
                              textColor=primary_color, spaceBefore=15, spaceAfter=8))
    styles.add(ParagraphStyle(name='NormalText', parent=styles['Normal'],
                              fontName='Helvetica', fontSize=11,
                              textColor=text_color, spaceBefore=4, spaceAfter=4, leading=14))
    styles.add(ParagraphStyle(name='Footer', parent=styles['Normal'],
                              fontName='Helvetica', fontSize=9,
                              textColor=colors.gray, alignment=1))
    return styles

def create_table(data):
    table = Table(data, colWidths=[2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f4f0ff')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#6d28d9')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('TEXTCOLOR', (0,1), (-1,-1), colors.HexColor('#0d0d12')),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 10),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#ede9fe')),
        ('PADDING', (0,0), (-1,-1), 8),
    ]))
    return table

def generate_terms_and_conditions_content(styles):
    return [
        PageBreak(),
        Paragraph("Borrow Box - Terms & Conditions", styles['CustomTitle']),
        Spacer(1, 10),
        Paragraph("1. General Obligations", styles['SectionHeader']),
        Paragraph("By using Borrow Box, both the renter and owner agree to conduct transactions in good faith. The item should be used reasonably and returned in its original condition.", styles['NormalText']),
        Paragraph("2. Liability and Damages", styles['SectionHeader']),
        Paragraph("The renter is fully responsible for any damages incurred during the rental period. Borrow Box holds the security deposit and reserves the right to compensate the owner in case of loss or damage. Disputes will be settled via the platform's support.", styles['NormalText']),
        Paragraph("3. Late Returns", styles['SectionHeader']),
        Paragraph("Items returned after the agreed rental period may be subject to late fees, deducted directly from the security deposit or billed additionally.", styles['NormalText']),
        Paragraph("4. Cancellation Policy", styles['SectionHeader']),
        Paragraph("Cancellations made within 24 hours of the start time may not be fully refunded. Check the specific cancellation policy listed on the item.", styles['NormalText']),
        Paragraph("5. Identification & Verification", styles['SectionHeader']),
        Paragraph("Renters must provide valid government-issued ID proof on request for high-value items.", styles['NormalText']),
        Spacer(1, 40),
        Paragraph("Thank you for using Borrow Box. We build trust by ensuring fair play.", styles['Footer']),
    ]

def main():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = get_pdf_styles()

    story = []

    # Title
    story.append(Paragraph("Booking Confirmation", styles['CustomTitle']))
    story.append(Paragraph("Thank you for using Borrow Box!", styles['Subtitle']))
    story.append(Spacer(1, 0.2*inch))

    # Booking Details
    story.append(Paragraph("Booking Details", styles['SectionHeader']))
    booking_data = [
        ["Item Name", "Sony A7III Camera"],
        ["Location / City", "Mumbai, India"],
        ["Dates", "2026-04-01 to 2026-04-05 (4 days)"],
        ["Total Amount", "IRS 4500.00"]
    ]
    story.append(create_table(booking_data))
    story.append(Spacer(1, 0.2*inch))

    # Renter Details
    story.append(Paragraph("Buyer Details", styles['SectionHeader']))
    buyer_data = [
        ["Name", "John Doe"],
        ["Contact Number", "+91 9876543210"],
        ["ID Proof Number", "AADHAAR 1234 5678"],
        ["Email", "john@example.com"]
    ]
    story.append(create_table(buyer_data))
    story.append(Spacer(1, 0.2*inch))

    # Owner Details
    story.append(Paragraph("Owner Details", styles['SectionHeader']))
    seller_data = [
        ["Name", "Jane Smith"],
        ["Contact Number", "+91 8765432109"],
        ["Email", "jane@example.com"]
    ]
    story.append(create_table(seller_data))

    # Terms and Conditions
    story.extend(generate_terms_and_conditions_content(styles))

    doc.build(story)
    with open('test_output.pdf', 'wb') as f:
        f.write(buffer.getvalue())
    print("PDF generated successfully.")

if __name__ == "__main__":
    main()
