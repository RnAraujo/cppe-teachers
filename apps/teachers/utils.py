from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.conf import settings
from datetime import date, datetime
from PIL import Image
import qrcode
import calendar
import io
import os

def generate_vigency_certificate_pdf(teacher):
    now = datetime.now()

    last_contribution = teacher.contributions.order_by('-payment_date').first()
    if last_contribution:
        last_day = calendar.monthrange(last_contribution.year, last_contribution.month)[1]
        last_date = date(last_contribution.year, last_contribution.month, last_day)
        today = date.today()
        if today <= last_date:
            days_left = (last_date - today).days
            vigency_text = f"Vigente hasta el {last_date.strftime('%d/%m/%Y')} (faltan {days_left} días)"
        else:
            vigency_text = f"Vigencia expirada desde {last_date.strftime('%d/%m/%Y')}"
    else:
        vigency_text = "Sin aportes registrados"


    # setting url and create qr code
    qr = qrcode.QRCode(version=2, box_size=10, border=4)
    data = 'https://colegiados.cppe-puno.org.pe/certificate/' + str(teacher.id)
    qr.add_data(data)

    qr_data = qr.make_image(fill_color='black', back_color='white')
    qr_buffer = io.BytesIO()
    qr_data.save(qr_buffer)
    qr_buffer.seek(0)
    qr_picture = Image.open(qr_buffer)

    # setting page format
    buffer = io.BytesIO() 
    p = canvas.Canvas(buffer, pagesize=A4)
    p_width, p_height = A4
    p.setTitle('Certificado de Habilidad')
    p.setAuthor('PING TO LOCAHOST EIRL')

    # setting front side
    front_side = os.path.join(settings.MEDIA_ROOT, 'background.jpg')
    p.drawImage(front_side, 0, 0, width=p_width, height=p_height)

    p.setFont('Helvetica', 10)
    p.drawString(115, 300, vigency_text)

    # setting fullname
    p.setFont('Helvetica-Bold', 16)
    p.drawCentredString(300, 430, teacher.full_name())

    # setting registration code
    p.setFont('Helvetica-Bold', 16)
    p.drawCentredString(300, 375, teacher.registration_code)

    # draw qr code
    size = 70
    p.drawInlineImage(qr_picture, 450, 460, size, size)

    p.setFont('Helvetica', 8)
    p.drawString(130, 100, f"Este documento fue generado electrónicamente. Emitido el {now.strftime('%d/%m/%Y')} a las {now.strftime('%H:%M')}")

    p.save()
    #buffer.seek(0)
    #buffer.close()

    # create_filename = f"Certificate_{teacher.id:07d}.pdf"

    # return FileResponse(buffer, as_attachment=False, filename=create_filename)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

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