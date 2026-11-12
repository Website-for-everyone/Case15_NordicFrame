"""
Nordic Frame — ReportLab Architectural Estimate PDF Generator
Builds a professional, print-ready commercial estimate PDF.
"""

import io
from datetime import datetime
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_estimate_pdf(estimate_data: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1F2421')
    )
    
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#707A74')
    )
    
    heading_style = ParagraphStyle(
        'HeadingSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#2C423B'),
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2421')
    )

    story = []

    # Header
    story.append(Paragraph("<b>NORDIC FRAME</b> &bull; SCANDINAVIAN MODULAR ARCHITECTURE", title_style))
    story.append(Paragraph(f"Commercial Project Estimate &bull; Ref: {estimate_data.get('estimate_number', 'NF-10001')}", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#2C423B'), spaceAfter=15))

    # Client & Date Meta Table
    client_meta = [
        [Paragraph(f"<b>Client:</b> {estimate_data.get('client_name', 'Client')}", body_style),
         Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}", body_style)],
        [Paragraph(f"<b>Contact:</b> {estimate_data.get('phone', 'N/A')}", body_style),
         Paragraph("<b>Validity:</b> 30 calendar days", body_style)]
    ]
    meta_table = Table(client_meta, colWidths=[260, 260])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F4F6F4')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # Base Module Specifications
    story.append(Paragraph("1. Base House Module", heading_style))
    base = estimate_data.get("base", {})
    base_rows = [
        ["Model", "Living Area", "Bedrooms", "Bathrooms", "Dimensions", "Base Price"],
        [base.get("name", "Studio 35"),
         f"{base.get('area_sqm', 35)} sq.m",
         str(base.get('bedrooms', 1)),
         str(base.get('bathrooms', 1)),
         base.get("dimensions", "7.0 x 5.0 m"),
         f"{base.get('base_price_rub', 2450000):,} RUB".replace(",", " ")]
    ]
    base_table = Table(base_rows, colWidths=[120, 80, 70, 70, 90, 90])
    base_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2C423B')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D5DDD7')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(base_table)
    story.append(Spacer(1, 15))

    # Selected Add-ons
    story.append(Paragraph("2. Selected Architectural Add-on Modules", heading_style))
    addons = estimate_data.get("addons", [])
    if addons:
        addon_rows = [["Component", "Category", "Additional Area", "Component Price"]]
        for a in addons:
            addon_rows.append([
                a.get("name", "Addon"),
                a.get("category", "General").capitalize(),
                f"+{a.get('area_sqm', 0)} sq.m" if a.get('area_sqm', 0) > 0 else "N/A",
                f"{a.get('price_rub', 0):,} RUB".replace(",", " ")
            ])
        addon_table = Table(addon_rows, colWidths=[240, 100, 90, 90])
        addon_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A6158')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8.5),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D5DDD7')),
            ('PADDING', (0,0), (-1,-1), 5)
        ]))
        story.append(addon_table)
    else:
        story.append(Paragraph("<i>Standard configuration without optional add-ons selected.</i>", body_style))
    story.append(Spacer(1, 15))

    # Bill of Materials & Cost Breakdown
    story.append(Paragraph("3. Bill of Materials (BOM) & Budget Breakdown", heading_style))
    bom = estimate_data.get("bom", {})
    bom_rows = [
        ["Budget Category", "Share", "Subtotal"],
        ["CLT Frame, Insulation & Structural Elements", "45%", f"{bom.get('materials_rub', 0):,} RUB".replace(",", " ")],
        ["Panoramic Glazing & Exterior Windows", "15%", f"{bom.get('glazing_rub', 0):,} RUB".replace(",", " ")],
        ["Engineering Networks, HVAC & Electrics", "20%", f"{bom.get('engineering_rub', 0):,} RUB".replace(",", " ")],
        ["Factory Assembly, Logistics & On-site Erection", "20%", f"{bom.get('assembly_rub', 0):,} RUB".replace(",", " ")],
        ["TOTAL INVESTMENT (TURNKEY)", "100%", f"{estimate_data.get('total_price_rub', 0):,} RUB".replace(",", " ")]
    ]
    bom_table = Table(bom_rows, colWidths=[300, 80, 140])
    bom_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F2421')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#E9E2D8')),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#C8D0CA')),
        ('PADDING', (0,0), (-1,-1), 6)
    ]))
    story.append(bom_table)
    story.append(Spacer(1, 20))

    # Warranty notice
    story.append(Paragraph(
        "<b>Warranty & Quality Guarantees:</b><br/>"
        "25-year structural warranty on cross-laminated timber (CLT) frame.<br/>"
        "5-year comprehensive warranty on engineering installations and weatherproofing.<br/>"
        "Manufactured in accordance with European timber construction standards (EN 1995-1-1).",
        body_style
    ))
    story.append(Spacer(1, 15))
    story.append(Paragraph("Nordic Frame Architecture Bureau &bull; Helsinki &bull; St. Petersburg &bull; Moscow", subtitle_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
