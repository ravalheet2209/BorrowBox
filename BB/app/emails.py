import os
from io import BytesIO
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils.timezone import now

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas as pdfcanvas

# ─────────────────────────────────────────────────────────
#  BRAND COLOURS
# ─────────────────────────────────────────────────────────
BRAND_PURPLE      = colors.HexColor('#6d28d9')
BRAND_LIGHT       = colors.HexColor('#ede9fe')
BRAND_DARK        = colors.HexColor('#4c1d95')
ACCENT_GREEN      = colors.HexColor('#059669')
ACCENT_ORANGE     = colors.HexColor('#d97706')
TEXT_DARK         = colors.HexColor('#1e1b4b')
TEXT_MID          = colors.HexColor('#4b5563')
TEXT_LIGHT        = colors.HexColor('#9ca3af')
WHITE             = colors.HexColor('#ffffff')
BG_SECTION        = colors.HexColor('#f5f3ff')
BORDER_LIGHT      = colors.HexColor('#ddd6fe')
ROW_ALT           = colors.HexColor('#faf5ff')
DANGER_RED        = colors.HexColor('#dc2626')

PAGE_W, PAGE_H    = A4
MARGIN_LR         = 18 * mm
MARGIN_TB         = 18 * mm
CONTENT_W         = PAGE_W - 2 * MARGIN_LR


# ─────────────────────────────────────────────────────────
#  PARAGRAPH STYLES
# ─────────────────────────────────────────────────────────
def _styles():
    s = getSampleStyleSheet()
    def add(name, **kw):
        if name not in s:
            s.add(ParagraphStyle(name=name, **kw))
    add('BB_Title',
        fontName='Helvetica-Bold', fontSize=22, textColor=WHITE,
        alignment=TA_CENTER, spaceAfter=2, leading=28)
    add('BB_SubTitle',
        fontName='Helvetica', fontSize=11, textColor=colors.HexColor('#c4b5fd'),
        alignment=TA_CENTER, spaceAfter=0, leading=15)
    add('BB_SectionTitle',
        fontName='Helvetica-Bold', fontSize=12, textColor=BRAND_PURPLE,
        spaceBefore=6, spaceAfter=4, leading=16)
    add('BB_Normal',
        fontName='Helvetica', fontSize=10, textColor=TEXT_DARK,
        spaceBefore=2, spaceAfter=2, leading=14)
    add('BB_Small',
        fontName='Helvetica', fontSize=8.5, textColor=TEXT_MID,
        spaceBefore=1, spaceAfter=1, leading=12)
    add('BB_Bold',
        fontName='Helvetica-Bold', fontSize=10, textColor=TEXT_DARK,
        spaceBefore=2, spaceAfter=2, leading=14)
    add('BB_Footer',
        fontName='Helvetica', fontSize=8, textColor=TEXT_LIGHT,
        alignment=TA_CENTER, leading=11)
    add('BB_Label',
        fontName='Helvetica-Bold', fontSize=9, textColor=BRAND_PURPLE,
        leading=13)
    add('BB_Value',
        fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
        leading=13)
    add('BB_TC_Head',
        fontName='Helvetica-Bold', fontSize=11, textColor=BRAND_DARK,
        spaceBefore=10, spaceAfter=3, leading=15)
    add('BB_TC_Body',
        fontName='Helvetica', fontSize=9, textColor=TEXT_MID,
        spaceBefore=2, spaceAfter=4, leading=13)
    add('BB_Amount',
        fontName='Helvetica-Bold', fontSize=18, textColor=ACCENT_GREEN,
        alignment=TA_CENTER, spaceAfter=2, leading=24)
    add('BB_AmountLabel',
        fontName='Helvetica', fontSize=9, textColor=TEXT_MID,
        alignment=TA_CENTER, leading=13)
    return s


# ─────────────────────────────────────────────────────────
#  CANVAS CALLBACKS  (header & footer drawn on every page)
# ─────────────────────────────────────────────────────────
class _HeaderFooter:
    """Passed as onFirstPage / onLaterPages to SimpleDocTemplate.build()."""

    def __init__(self, doc_title: str, subtitle: str = ''):
        self.doc_title = doc_title
        self.subtitle  = subtitle

    def __call__(self, c: pdfcanvas.Canvas, doc):
        self._draw_header(c, doc)
        self._draw_footer(c, doc)

    def _draw_header(self, c: pdfcanvas.Canvas, doc):
        w, h = A4
        hdr_h = 28 * mm

        # gradient-like header band (drawn as two rectangles)
        c.setFillColor(BRAND_DARK)
        c.rect(0, h - hdr_h, w, hdr_h, stroke=0, fill=1)
        c.setFillColor(BRAND_PURPLE)
        c.rect(0, h - hdr_h, w * 0.6, hdr_h, stroke=0, fill=1)

        # logo pill  ●  BB
        pill_x, pill_y = MARGIN_LR, h - hdr_h + (hdr_h - 8 * mm) / 2
        c.setFillColor(WHITE)
        c.roundRect(pill_x, pill_y, 22 * mm, 8 * mm, 3 * mm, stroke=0, fill=1)
        c.setFillColor(BRAND_PURPLE)
        c.setFont('Helvetica-Bold', 11)
        c.drawCentredString(pill_x + 11 * mm, pill_y + 2.2 * mm, 'BB')

        # Title
        c.setFillColor(WHITE)
        c.setFont('Helvetica-Bold', 16)
        c.drawString(pill_x + 26 * mm, h - hdr_h + (hdr_h - 6 * mm) / 2 + 2, self.doc_title)

        # Subtitle (right-aligned)
        if self.subtitle:
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#c4b5fd'))
            c.drawRightString(w - MARGIN_LR, h - hdr_h + (hdr_h - 6 * mm) / 2 + 2, self.subtitle)

        # thin accent line below header
        c.setStrokeColor(colors.HexColor('#8b5cf6'))
        c.setLineWidth(1.5)
        c.line(0, h - hdr_h, w, h - hdr_h)

    def _draw_footer(self, c: pdfcanvas.Canvas, doc):
        w, _ = A4
        fy = 10 * mm

        c.setStrokeColor(BORDER_LIGHT)
        c.setLineWidth(0.5)
        c.line(MARGIN_LR, fy + 5 * mm, w - MARGIN_LR, fy + 5 * mm)

        c.setFont('Helvetica', 7.5)
        c.setFillColor(TEXT_LIGHT)
        c.drawString(MARGIN_LR, fy + 1.5 * mm,
                     '© 2025 Borrow Box · Empowering Peer-to-Peer Rentals')
        c.drawRightString(w - MARGIN_LR, fy + 1.5 * mm,
                          f'Page {doc.page}  ·  {now().strftime("%d %b %Y")}')


# ─────────────────────────────────────────────────────────
#  REUSABLE BUILDING BLOCKS
# ─────────────────────────────────────────────────────────
def _divider(color=BORDER_LIGHT, thickness=0.5):
    return HRFlowable(width='100%', thickness=thickness,
                      color=color, spaceAfter=4, spaceBefore=4)


def _section_header(title: str, styles, icon: str = '▸'):
    """Coloured section-header strip."""
    data = [[f'{icon}  {title}']]
    t = Table(data, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, -1), BRAND_LIGHT),
        ('TEXTCOLOR',   (0, 0), (-1, -1), BRAND_DARK),
        ('FONTNAME',    (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 11),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING',  (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW',   (0, 0), (-1, -1), 1.5, BRAND_PURPLE),
    ]))
    return t


def _info_table(rows: list, col1_w=65 * mm):
    """Two-column label → value table with alternating rows."""
    col2_w = CONTENT_W - col1_w
    table_data = [[Paragraph(f'<b>{label}</b>', ParagraphStyle(
                        'TmpLbl', fontName='Helvetica-Bold', fontSize=9,
                        textColor=BRAND_PURPLE, leading=13)),
                   Paragraph(str(value), ParagraphStyle(
                        'TmpVal', fontName='Helvetica', fontSize=9,
                        textColor=TEXT_DARK, leading=13))]
                  for label, value in rows]

    t = Table(table_data, colWidths=[col1_w, col2_w])
    style_cmds = [
        ('ALIGN',         (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW',     (0, 0), (-1, -2), 0.5, BORDER_LIGHT),
        ('BOX',           (0, 0), (-1, -1), 0.5, BORDER_LIGHT),
    ]
    for i in range(len(table_data)):
        bg = ROW_ALT if i % 2 == 0 else WHITE
        style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))

    t.setStyle(TableStyle(style_cmds))
    return t


def _amount_badge(amount_str: str, label: str):
    """A centred badge showing the monetary amount."""
    data = [[amount_str], [label]]
    t = Table(data, colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), BG_SECTION),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING',    (0, 0), (0,  0),  10),
        ('BOTTOMPADDING', (0, 0), (0,  0),  2),
        ('TOPPADDING',    (0, 1), (0,  1),  2),
        ('BOTTOMPADDING', (0, 1), (0,  1),  10),
        ('FONTNAME',      (0, 0), (0,  0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (0,  0),  24),
        ('TEXTCOLOR',     (0, 0), (0,  0),  ACCENT_GREEN),
        ('FONTNAME',      (0, 1), (0,  1),  'Helvetica'),
        ('FONTSIZE',      (0, 1), (0,  1),  9),
        ('TEXTCOLOR',     (0, 1), (0,  1),  TEXT_MID),
        ('BOX',           (0, 0), (-1, -1), 1, BORDER_LIGHT),
    ]))
    return t


def _status_badge(text: str, color=ACCENT_GREEN):
    data = [[text]]
    t = Table(data, colWidths=[45 * mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), color),
        ('TEXTCOLOR',     (0, 0), (-1, -1), WHITE),
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('ROUNDEDCORNERS', [3]),
    ]))
    return t


# ─────────────────────────────────────────────────────────
#  TERMS & CONDITIONS  (reusable content block)
# ─────────────────────────────────────────────────────────
def _tc_content(styles):
    clauses = [
        ("1. General Obligations",
         "By using Borrow Box, both the renter and owner agree to conduct transactions in good "
         "faith. The item must be used responsibly and returned in its original condition, "
         "including any accessories provided."),
        ("2. Liability & Damages",
         "The renter is fully responsible for any damage, loss, or theft during the rental "
         "period. Borrow Box reserves the right to utilise the security deposit to compensate "
         "the owner. Disputes will be escalated to Borrow Box Support for independent resolution."),
        ("3. Late Returns",
         "Items returned after the agreed end date are subject to additional charges calculated "
         "at the daily rental rate or as specified by the owner. Continued late returns may lead "
         "to account suspension."),
        ("4. Cancellation Policy",
         "Cancellations made more than 48 hours before the rental start date are eligible for a "
         "full refund. Cancellations within 48 hours may incur a cancellation fee of up to 50% "
         "of the total amount. No refund is applicable for no-shows."),
        ("5. Identification & Verification",
         "Renters must provide a valid government-issued photo ID before collecting any "
         "high-value item. Borrow Box may store a masked copy of the ID number for dispute-"
         "resolution purposes only."),
        ("6. Security Deposit",
         "A refundable security deposit is held by Borrow Box during the rental period. It is "
         "released within 3–5 business days after a satisfactory return, less any applicable "
         "deductions for damage or late fees."),
        ("7. Platform Fees",
         "Borrow Box charges a platform fee on every completed transaction. This fee is "
         "non-refundable and is clearly communicated prior to checkout."),
        ("8. Governing Law",
         "These Terms are governed by the laws of India. Any disputes arising shall be subject "
         "to the exclusive jurisdiction of courts located in the relevant state."),
    ]
    content = [
        Spacer(1, 4),
        Paragraph(
            "Please read these Terms & Conditions carefully. By completing a booking on "
            "Borrow Box you confirm that you have read, understood, and agreed to all the "
            "terms outlined below.",
            ParagraphStyle('TC_Intro', fontName='Helvetica', fontSize=9,
                           textColor=TEXT_MID, leading=13, spaceAfter=6)),
        _divider(BRAND_PURPLE, 1),
        Spacer(1, 4),
    ]
    for heading, body in clauses:
        content.append(
            Paragraph(heading, ParagraphStyle(
                'TCH', fontName='Helvetica-Bold', fontSize=10,
                textColor=BRAND_DARK, spaceBefore=8, spaceAfter=3, leading=14)))
        content.append(
            Paragraph(body, ParagraphStyle(
                'TCB', fontName='Helvetica', fontSize=9,
                textColor=TEXT_MID, spaceAfter=4, leading=13)))

    content.append(Spacer(1, 12))
    content.append(_divider(BORDER_LIGHT))
    content.append(
        Paragraph(
            'I acknowledge that I have read and agree to the Borrow Box Terms & Conditions.',
            ParagraphStyle('TC_Ack', fontName='Helvetica-Oblique', fontSize=9,
                           textColor=TEXT_MID, alignment=TA_CENTER, leading=13)))
    content.append(Spacer(1, 20))

    sig_data = [['Renter Signature', '', 'Date', '']]
    sig_t = Table(sig_data, colWidths=[40*mm, 60*mm, 20*mm, 45*mm])
    sig_t.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8.5),
        ('TEXTCOLOR',     (0, 0), (-1, -1), TEXT_MID),
        ('LINEBELOW',     (1, 0), (1, 0),   0.8, TEXT_MID),
        ('LINEBELOW',     (3, 0), (3, 0),   0.8, TEXT_MID),
        ('VALIGN',        (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    content.append(sig_t)
    return content


# ─────────────────────────────────────────────────────────
#  PUBLIC API  –  send_deposit_email
# ─────────────────────────────────────────────────────────
def send_deposit_email(user, amount, action_type, new_balance):
    """
    Sends a professional PDF receipt for security deposit additions / withdrawals.
    """
    if not user.email:
        return

    is_add    = action_type.lower() in ('add', 'added', 'addition')
    action_lbl = 'Addition' if is_add else 'Withdrawal'
    accent     = ACCENT_GREEN if is_add else ACCENT_ORANGE
    subject    = f'Borrow Box – Security Deposit {action_lbl} Receipt'

    buffer = BytesIO()
    hf     = _HeaderFooter(f'Security Deposit {action_lbl}',
                            subtitle=f'Receipt · {now().strftime("%d %b %Y %H:%M")}')
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_LR, leftMargin=MARGIN_LR,
        topMargin=35 * mm, bottomMargin=22 * mm,
        title=subject,
    )
    styles = _styles()
    story  = []

    # ── Amount highlight
    story.append(Spacer(1, 4))
    story.append(_amount_badge(f'IRS {amount}', f'Amount {action_lbl}'))
    story.append(Spacer(1, 10))

    # ── Transaction Details
    story.append(_section_header('Transaction Details', styles, '📄'))
    story.append(Spacer(1, 4))
    profile = getattr(user, 'profile', None)
    rows = [
        ('Transaction Date',  now().strftime('%d %B %Y, %H:%M UTC')),
        ('Transaction Type',  action_lbl),
        ('Reference No.',     f'BB-DEP-{now().strftime("%Y%m%d%H%M%S")}'),
        ('Status',            '✔ Successful'),
    ]
    story.append(_info_table(rows))
    story.append(Spacer(1, 10))

    # ── Account Details
    story.append(_section_header('Account Details', styles, '👤'))
    story.append(Spacer(1, 4))
    acc_rows = [
        ('Full Name',         f'{user.first_name} {user.last_name}'.strip() or user.username),
        ('Username',          user.username),
        ('Email Address',     user.email),
        ('Phone',             getattr(profile, 'phone', None) or 'N/A'),
        ('Amount Transacted', f'IRS {amount}'),
        ('New Deposit Balance', f'IRS {new_balance}'),
    ]
    story.append(_info_table(acc_rows))
    story.append(Spacer(1, 16))

    # ── Note
    note_data = [[
        Paragraph(
            f'<b>Note:</b> Your security deposit balance has been successfully '
            f'{"credited" if is_add else "debited"} by <b>IRS {amount}</b>. '
            f'Your new available deposit balance is <b>IRS {new_balance}</b>. '
            f'This amount acts as collateral for future rentals on Borrow Box.',
            ParagraphStyle('Note', fontName='Helvetica', fontSize=9,
                           textColor=TEXT_DARK, leading=13))
    ]]
    note_t = Table(note_data, colWidths=[CONTENT_W])
    note_t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), BG_SECTION),
        ('LEFTPADDING',   (0, 0), (-1, -1), 10),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
        ('TOPPADDING',    (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('BOX',           (0, 0), (-1, -1), 1, BRAND_PURPLE),
    ]))
    story.append(note_t)
    story.append(Spacer(1, 16))
    story.append(_divider())
    story.append(
        Paragraph('Thank you for choosing <b>Borrow Box</b>. '
                  'This is a system-generated receipt – no signature required.',
                  styles['BB_Footer']))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    pdf = buffer.getvalue()
    buffer.close()

    body = (
        f'Hello {user.first_name or user.username},\n\n'
        f'Your security deposit has been successfully '
        f'{"credited" if is_add else "debited"} by IRS {amount}.\n'
        f'New balance: IRS {new_balance}\n\n'
        f'Please find the official receipt attached as a PDF.\n\n'
        f'Regards,\nThe Borrow Box Team'
    )
    mail = EmailMultiAlternatives(
        subject, body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@borrowbox.com'),
        [user.email]
    )
    mail.attach(f'deposit_{action_type}_receipt.pdf', pdf, 'application/pdf')
    try:
        mail.send(fail_silently=True)
    except Exception as e:
        print(f'[BorrowBox] Failed to send deposit email: {e}')


# ─────────────────────────────────────────────────────────
#  PUBLIC API  –  send_booking_buyer_email
# ─────────────────────────────────────────────────────────
def send_booking_buyer_email(booking, buyer, seller):
    if not buyer.email:
        return

    days = max((booking.end_date - booking.start_date).days, 1)
    subject = f'Borrow Box – Booking Confirmed: {booking.item.title}'

    buffer = BytesIO()
    hf = _HeaderFooter('Booking Confirmation',
                        subtitle=f'Ref# BB-{booking.id:06d}')
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_LR, leftMargin=MARGIN_LR,
        topMargin=35 * mm, bottomMargin=22 * mm,
        title=subject,
    )
    styles = _styles()
    story  = []

    # ── Greeting
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            f'Congratulations, <b>{buyer.first_name or buyer.username}</b>! '
            f'Your booking is <font color="#059669"><b>Confirmed</b></font>.',
            ParagraphStyle('Greet', fontName='Helvetica', fontSize=12,
                           textColor=TEXT_DARK, leading=17, spaceAfter=4)))
    story.append(Spacer(1, 6))

    # ── Amount highlight
    story.append(_amount_badge(f'IRS {booking.total_price}', 'Total Booking Amount'))
    story.append(Spacer(1, 12))

    # ── Booking Details
    story.append(_section_header('Booking Details', styles, '📋'))
    story.append(Spacer(1, 4))
    b_rows = [
        ('Booking Reference',  f'BB-{booking.id:06d}'),
        ('Booking Date',       now().strftime('%d %B %Y, %H:%M UTC')),
        ('Item Name',          booking.item.title),
        ('Category',           str(booking.item.category) if booking.item.category else 'N/A'),
        ('City / Location',    booking.item.location),
        ('Rental Start Date',  booking.start_date.strftime('%d %B %Y')),
        ('Rental End Date',    booking.end_date.strftime('%d %B %Y')),
        ('Duration',           f'{days} Day{"s" if days != 1 else ""}'),
        ('Price Per Day',      f'IRS {booking.item.price_per_day}'),
        ('Total Amount',       f'IRS {booking.total_price}'),
        ('Booking Status',     '✔ Confirmed'),
    ]
    story.append(_info_table(b_rows))
    story.append(Spacer(1, 12))

    # ── Owner / Seller Details
    story.append(_section_header('Owner Details', styles, '🏠'))
    story.append(Spacer(1, 4))
    s_profile = getattr(seller, 'profile', None)
    s_rows = [
        ('Owner Name',    f'{seller.first_name} {seller.last_name}'.strip() or seller.username),
        ('Username',      seller.username),
        ('Email Address', seller.email),
        ('Phone',         getattr(s_profile, 'phone', None) or 'N/A'),
        ('Address',       getattr(s_profile, 'address', None) or 'N/A'),
    ]
    story.append(_info_table(s_rows))
    story.append(Spacer(1, 12))

    # ── Buyer Details
    story.append(_section_header('Your (Renter) Details', styles, '👤'))
    story.append(Spacer(1, 4))
    b_profile = getattr(buyer, 'profile', None)
    masked_id = (b_profile.mask_id_number()
                 if b_profile and hasattr(b_profile, 'mask_id_number') else 'N/A')
    by_rows = [
        ('Your Name',      f'{buyer.first_name} {buyer.last_name}'.strip() or buyer.username),
        ('Username',       buyer.username),
        ('Email Address',  buyer.email),
        ('Phone',          getattr(b_profile, 'phone', None) or 'N/A'),
        ('ID Proof No.',   masked_id),
    ]
    story.append(_info_table(by_rows))
    story.append(Spacer(1, 12))

    # ── Important Instructions
    story.append(_section_header('Important Instructions', styles, '⚠'))
    story.append(Spacer(1, 4))
    instructions = [
        '• Please carry a valid government-issued Photo ID and this PDF at the time of item collection.',
        '• Inspect the item thoroughly before accepting it. Raise any concerns immediately.',
        '• Ensure the item is returned by <b>' + booking.end_date.strftime('%d %B %Y') + '</b> to avoid late charges.',
        '• In case of any issues contact Borrow Box Support immediately.',
        '• Your security deposit will be released within 3–5 business days of a satisfactory return.',
    ]
    for line in instructions:
        story.append(
            Paragraph(line, ParagraphStyle(
                'Inst', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
                leading=14, spaceAfter=3, leftIndent=4)))
    story.append(Spacer(1, 10))
    story.append(_divider())
    story.append(
        Paragraph('This is a system-generated document. '
                  'For support: support@borrowbox.com  |  www.borrowbox.com',
                  styles['BB_Footer']))

    # ── Terms & Conditions (new page)
    story.append(PageBreak())
    story.append(_section_header('Terms & Conditions', styles, '📜'))
    story.extend(_tc_content(styles))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    pdf = buffer.getvalue()
    buffer.close()

    body = (
        f'Hello {buyer.first_name or buyer.username},\n\n'
        f'Your booking for "{booking.item.title}" has been confirmed!\n\n'
        f'  Item      : {booking.item.title}\n'
        f'  Location  : {booking.item.location}\n'
        f'  Dates     : {booking.start_date.strftime("%d %b %Y")} '
        f'→ {booking.end_date.strftime("%d %b %Y")} ({days} days)\n'
        f'  Amount    : IRS {booking.total_price}\n\n'
        f'Please find the complete booking confirmation with Terms & Conditions attached as a PDF.\n\n'
        f'Thank you for choosing Borrow Box!\n'
        f'The Borrow Box Team'
    )
    mail = EmailMultiAlternatives(
        subject, body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@borrowbox.com'),
        [buyer.email]
    )
    mail.attach('booking_confirmation.pdf', pdf, 'application/pdf')
    try:
        mail.send(fail_silently=True)
    except Exception as e:
        print(f'[BorrowBox] Failed to send buyer booking email: {e}')


# ─────────────────────────────────────────────────────────
#  PUBLIC API  –  send_booking_seller_email
# ─────────────────────────────────────────────────────────
def send_booking_seller_email(booking, buyer, seller):
    if not seller.email:
        return

    days = max((booking.end_date - booking.start_date).days, 1)
    subject = f'Borrow Box – New Booking Received: {booking.item.title}'

    buffer = BytesIO()
    hf = _HeaderFooter('New Booking Alert',
                        subtitle=f'Ref# BB-{booking.id:06d}')
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=MARGIN_LR, leftMargin=MARGIN_LR,
        topMargin=35 * mm, bottomMargin=22 * mm,
        title=subject,
    )
    styles = _styles()
    story  = []

    # ── Greeting
    story.append(Spacer(1, 2))
    story.append(
        Paragraph(
            f'Great news, <b>{seller.first_name or seller.username}</b>! '
            f'Your item <b>"{booking.item.title}"</b> has been booked.',
            ParagraphStyle('Greet2', fontName='Helvetica', fontSize=12,
                           textColor=TEXT_DARK, leading=17, spaceAfter=4)))
    story.append(Spacer(1, 6))

    # ── Expected Earnings badge
    story.append(_amount_badge(f'IRS {booking.total_price}', 'Expected Earnings'))
    story.append(Spacer(1, 12))

    # ── Booking Details
    story.append(_section_header('Booking Details', styles, '📋'))
    story.append(Spacer(1, 4))
    b_rows = [
        ('Booking Reference',    f'BB-{booking.id:06d}'),
        ('Booking Date',         now().strftime('%d %B %Y, %H:%M UTC')),
        ('Item Name',            booking.item.title),
        ('Category',             str(booking.item.category) if booking.item.category else 'N/A'),
        ('City / Location',      booking.item.location),
        ('Rental Start Date',    booking.start_date.strftime('%d %B %Y')),
        ('Rental End Date',      booking.end_date.strftime('%d %B %Y')),
        ('Duration',             f'{days} Day{"s" if days != 1 else ""}'),
        ('Price Per Day',        f'IRS {booking.item.price_per_day}'),
        ('Total Expected Payout', f'IRS {booking.total_price}'),
        ('Booking Status',       '✔ Confirmed'),
    ]
    story.append(_info_table(b_rows))
    story.append(Spacer(1, 12))

    # ── Renter (Buyer) Details
    story.append(_section_header('Renter Details', styles, '👤'))
    story.append(Spacer(1, 4))
    b_profile = getattr(buyer, 'profile', None)
    masked_id = (b_profile.mask_id_number()
                 if b_profile and hasattr(b_profile, 'mask_id_number') else 'N/A')
    by_rows = [
        ('Renter Name',    f'{buyer.first_name} {buyer.last_name}'.strip() or buyer.username),
        ('Username',       buyer.username),
        ('Email Address',  buyer.email),
        ('Phone',          getattr(b_profile, 'phone', None) or 'N/A'),
        ('ID Proof No.',   masked_id),
    ]
    story.append(_info_table(by_rows))
    story.append(Spacer(1, 12))

    # ── Action Required
    story.append(_section_header('Action Required', styles, '✅'))
    story.append(Spacer(1, 4))
    actions = [
        '• Ensure your item is clean, functional, and available from '
        f'<b>{booking.start_date.strftime("%d %B %Y")}</b>.',
        '• Verify the renter\'s government-issued Photo ID at the time of handover.',
        '• Document the item\'s condition with photos before handover.',
        '• Return the item\'s accessories and all components as listed.',
        '• Contact Borrow Box Support if the renter does not show up or encounters an issue.',
    ]
    for line in actions:
        story.append(
            Paragraph(line, ParagraphStyle(
                'Act', fontName='Helvetica', fontSize=9, textColor=TEXT_DARK,
                leading=14, spaceAfter=3, leftIndent=4)))

    story.append(Spacer(1, 10))
    story.append(_divider())
    story.append(
        Paragraph('This is a system-generated document. '
                  'For support: support@borrowbox.com  |  www.borrowbox.com',
                  styles['BB_Footer']))

    # ── Terms & Conditions (new page)
    story.append(PageBreak())
    story.append(_section_header('Terms & Conditions', styles, '📜'))
    story.extend(_tc_content(styles))

    doc.build(story, onFirstPage=hf, onLaterPages=hf)
    pdf = buffer.getvalue()
    buffer.close()

    body = (
        f'Hello {seller.first_name or seller.username},\n\n'
        f'Your item "{booking.item.title}" has been booked!\n\n'
        f'  Renter    : {buyer.first_name} {buyer.last_name} (@{buyer.username})\n'
        f'  Dates     : {booking.start_date.strftime("%d %b %Y")} '
        f'→ {booking.end_date.strftime("%d %b %Y")} ({days} days)\n'
        f'  Earnings  : IRS {booking.total_price}\n\n'
        f'Please ensure the item is ready and in good condition. '
        f'Full details are attached as a PDF.\n\n'
        f'Thank you for listing on Borrow Box!\n'
        f'The Borrow Box Team'
    )
    mail = EmailMultiAlternatives(
        subject, body,
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@borrowbox.com'),
        [seller.email]
    )
    mail.attach('new_booking_alert.pdf', pdf, 'application/pdf')
    try:
        mail.send(fail_silently=True)
    except Exception as e:
        print(f'[BorrowBox] Failed to send seller booking email: {e}')
