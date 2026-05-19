import django
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BB.settings')
django.setup()

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Spacer, Paragraph, PageBreak

from app.emails import (
    _HeaderFooter, _styles, _section_header, _info_table,
    _amount_badge, _tc_content, _divider,
    MARGIN_LR, TEXT_DARK
)

output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_email_preview.pdf')

with open(output_path, 'wb') as buffer:
    hf = _HeaderFooter('Booking Confirmation', subtitle='Ref# BB-000042')
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_LR, leftMargin=MARGIN_LR,
        topMargin=35 * mm, bottomMargin=22 * mm,
    )
    styles = _styles()
    story = []

    story.append(Spacer(1, 2))
    story.append(Paragraph(
        'Congratulations, <b>John</b>! Your booking is '
        '<font color="#059669"><b>Confirmed</b></font>.',
        ParagraphStyle('G', fontName='Helvetica', fontSize=12,
                       textColor=TEXT_DARK, leading=17, spaceAfter=4)
    ))
    story.append(Spacer(1, 6))
    story.append(_amount_badge('IRS 3,500', 'Total Booking Amount'))
    story.append(Spacer(1, 12))

    # Booking Details
    story.append(_section_header('Booking Details', styles, 'BOOKING'))
    story.append(Spacer(1, 4))
    story.append(_info_table([
        ('Booking Reference',  'BB-000042'),
        ('Booking Date',       '24 March 2025, 09:14 UTC'),
        ('Item Name',          'Sony Alpha A7 III Camera'),
        ('Category',           'Electronics'),
        ('City / Location',    'Ahmedabad, Gujarat'),
        ('Rental Start Date',  '28 March 2025'),
        ('Rental End Date',    '31 March 2025'),
        ('Duration',           '3 Days'),
        ('Price Per Day',      'IRS 1,000'),
        ('Total Amount',       'IRS 3,500'),
        ('Booking Status',     'Confirmed'),
    ]))
    story.append(Spacer(1, 12))

    # Owner Details
    story.append(_section_header('Owner Details', styles, 'OWNER'))
    story.append(Spacer(1, 4))
    story.append(_info_table([
        ('Owner Name',    'Ramesh Sharma'),
        ('Username',      'ramesh_s'),
        ('Email Address', 'ramesh@example.com'),
        ('Phone',         '+91 98765 43210'),
        ('Address',       'Satellite, Ahmedabad'),
    ]))
    story.append(Spacer(1, 12))

    # Renter Details
    story.append(_section_header('Your (Renter) Details', styles, 'RENTER'))
    story.append(Spacer(1, 4))
    story.append(_info_table([
        ('Your Name',     'John Doe'),
        ('Username',      'johndoe'),
        ('Email Address', 'john@example.com'),
        ('Phone',         '+91 99887 76655'),
        ('ID Proof No.',  '****5678'),
    ]))
    story.append(Spacer(1, 12))

    # Instructions
    story.append(_section_header('Important Instructions', styles, 'INFO'))
    story.append(Spacer(1, 4))
    for line in [
        '* Carry a valid government-issued Photo ID at the time of collection.',
        '* Inspect the item before accepting it and raise concerns immediately.',
        '* Return the item by 31 March 2025 to avoid late charges.',
        '* Security deposit released within 3-5 business days.',
    ]:
        story.append(Paragraph(
            line,
            ParagraphStyle('I', fontName='Helvetica', fontSize=9,
                           textColor=TEXT_DARK, leading=14, spaceAfter=3, leftIndent=4)
        ))

    story.append(Spacer(1, 10))
    story.append(_divider())
    story.append(Paragraph(
        'system-generated  |  support@borrowbox.com  |  www.borrowbox.com',
        styles['BB_Footer']
    ))

    # T&C page
    story.append(PageBreak())
    story.append(_section_header('Terms and Conditions', styles, 'T&C'))
    story.extend(_tc_content(styles))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)

print(f'PDF generated successfully: {output_path}')
