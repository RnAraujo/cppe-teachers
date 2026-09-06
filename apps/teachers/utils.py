from reportlab.lib.pagesizes import A5, A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import io

def generate_receipt_pdf(contribution):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A5,
                            rightMargin=10*mm, leftMargin=10*mm,
                            topMargin=10*mm, bottomMargin=10*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='Right', alignment=TA_RIGHT, fontSize=10))
    styles.add(ParagraphStyle(name='Title1', alignment=TA_CENTER, fontSize=16, spaceAfter=12, textColor=colors.HexColor('#00254a')))

    elements = []
    elements.append(Paragraph("COLEGIO DE PROFESORES DEL PERÚ", styles['Title']))
    elements.append(Paragraph("REGIÓN PUNO", styles['Center']))
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph(f"<b>N° {contribution.receipt_number}</b>", styles['Center']))
    elements.append(Spacer(1, 4*mm))

    teacher = contribution.teacher
    data = [
        ["DNI:", teacher.dni],
        ["Nombres:", teacher.first_name],
        ["Apellidos:", teacher.last_name],
        ["Código Colegiatura:", teacher.registration_code],
    ]
    table = Table(data, colWidths=[50*mm, 70*mm])
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 4*mm))

    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    mes_str = meses[contribution.month-1]
    data2 = [
        ["Concepto:", f"Aporte mensual - {mes_str} {contribution.year}"],
        ["Monto:", f"S/ {contribution.amount:.2f}"],
        ["Fecha de pago:", contribution.payment_date.strftime("%d/%m/%Y %H:%M")],
    ]
    table2 = Table(data2, colWidths=[50*mm, 70*mm])
    table2.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    elements.append(table2)
    elements.append(Spacer(1, 6*mm))

    if contribution.comments:
        elements.append(Paragraph(f"<b>Comentarios:</b> {contribution.comments}", styles['Normal']))
    if contribution.observations:
        elements.append(Paragraph(f"<b>Observaciones:</b> {contribution.observations}", styles['Normal']))

    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("Este comprobante es válido como constancia de pago.", styles['Normal']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_multiple_receipts_pdf(contributions):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=14, spaceAfter=6))
    styles.add(ParagraphStyle(name='Title1', alignment=TA_CENTER, fontSize=16, spaceAfter=12, textColor=colors.HexColor('#00254a')))

    elements = []
    elements.append(Paragraph("COLEGIO DE PROFESORES DEL PERÚ", styles['Title']))
    elements.append(Paragraph("REGIÓN PUNO - REPORTE DE APORTES", styles['Center']))
    elements.append(Spacer(1, 6*mm))

    data = [["N°", "Profesor", "Mes", "Año", "Monto", "Fecha Pago", "Comprobante"]]
    for idx, c in enumerate(contributions, start=1):
        teacher = c.teacher
        data.append([
            str(idx),
            f"{teacher.last_name} {teacher.first_name}",
            c.get_month_display(),
            str(c.year),
            f"S/ {c.amount:.2f}",
            c.payment_date.strftime("%d/%m/%Y"),
            c.receipt_number
        ])

    col_widths = [20*mm, 50*mm, 30*mm, 20*mm, 30*mm, 35*mm, 40*mm]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#00254a')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    elements.append(table)
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf