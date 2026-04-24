from io import BytesIO
from django.conf import settings
from django.template.loader import get_template
from django.core.mail import EmailMessage
from xhtml2pdf import pisa


# =========================
# Generate Invoice PDF (NO QR)
# =========================
def generate_invoice_pdf(booking):

    template = get_template("invoice.html")
    html = template.render({"booking": booking})

    result = BytesIO()
    pisa.CreatePDF(html, dest=result)

    return result.getvalue()


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
