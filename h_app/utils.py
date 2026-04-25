# from io import BytesIO
# from django.conf import settings
# from django.template.loader import get_template
# from django.core.mail import EmailMessage
# from xhtml2pdf import pisa


# # =========================
# # Generate Invoice PDF (NO QR)
# # =========================
# def generate_invoice_pdf(booking):

#     template = get_template("invoice.html")
#     html = template.render({"booking": booking})

#     result = BytesIO()
#     pisa.CreatePDF(html, dest=result)

#     return result.getvalue()


# # =========================
# # Send Email with Invoice
# # =========================
# def send_email_with_invoice(subject, message, booking):

#     if not booking.email:
#         return

#     email = EmailMessage(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [booking.email],
#     )

#     pdf = generate_invoice_pdf(booking)
#     email.attach(
#         f"invoice_{booking.id}.pdf",
#         pdf,
#         "application/pdf"
#     )

#     email.send(fail_silently=False)
from io import BytesIO
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# =========================
# Generate Invoice PDF
# =========================
def generate_invoice_pdf(booking):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, 750, "INVOICE")

    # Customer Details
    p.setFont("Helvetica", 12)
    p.drawString(100, 700, f"Booking ID: {booking.id}")
    p.drawString(100, 680, f"Name: {booking.name}")
    p.drawString(100, 660, f"Email: {booking.email}")
    p.drawString(100, 640, f"Amount: ₹{booking.amount}")

    # Line
    p.line(100, 630, 400, 630)

    # Footer
    p.drawString(100, 600, "Thank you for your booking!")

    p.save()

    buffer.seek(0)
    return buffer.getvalue()


# =========================
# Send Email with Invoice
# =========================
def send_email_with_invoice(subject, message, booking):
    if not booking.email:
        return

    email = EmailMessage(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [booking.email],
    )

    pdf = generate_invoice_pdf(booking)

    email.attach(
        f"invoice_{booking.id}.pdf",
        pdf,
        "application/pdf"
    )

    email.send(fail_silently=False)