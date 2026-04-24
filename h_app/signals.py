from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from .models import Booking, UserProfile
from .utils import send_email_with_invoice


# =====================================
# 1️⃣ AUTO CREATE USER PROFILE SIGNAL
# =====================================
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Save only if profile exists (handles first-time users)
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()


# =====================================
# 2️⃣ BOOKING CONFIRMED → SEND INVOICE EMAIL
# =====================================
@receiver(post_save, sender=Booking)
def booking_status_change_email(sender, instance, created, **kwargs):
    """
    📧 Send invoice email ONLY when booking status becomes CONFIRMED
    """

    # 🛑 Do NOT send email on new booking creation
    if created:
        return

    # 🛑 Do NOT send email if status not confirmed
    if instance.status != 'confirmed':
        return

    # 📧 Subject + Message
    subject = "Payment Successful – Booking Confirmed"

    message = f"""
Hello {instance.name},

Your payment was successful 🎉
Your booking is now CONFIRMED.

Hotel: {instance.room.hotel.name}
Room: {instance.room.room_name} ({instance.room.view_type} View)
Check-in: {instance.check_in}
Check-out: {instance.check_out}
Total Nights: {instance.total_nights}
Total Amount: ₹{instance.total_amount}

Your invoice is attached with this email.

Thank you for booking with us!
Hotel Management System
"""

    # 📎 Send email with attached invoice PDF
    send_email_with_invoice(subject, message, instance)

