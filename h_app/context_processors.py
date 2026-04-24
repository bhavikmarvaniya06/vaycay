from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import (
    Wishlist,
    Hotel,
    Room,
    Booking,
    Review,
    ContactMessage,
    NearbyPlace
)

def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        count = 0
    return {"wishlist_count": count}


def admin_counts(request):

    # =====================
    # 📈 Revenue Overview
    # =====================
    revenue_qs = (
        Booking.objects
        .filter(is_paid=True)
        .annotate(month=TruncMonth("booked_on"))
        .values("month")
        .annotate(total=Sum("total_amount"))
        .order_by("month")
    )

    total_revenue = (
        Booking.objects
        .filter(is_paid=True)
        .aggregate(total=Sum("total_amount"))["total"] or 0
    )

    # =====================
    # ⭐ Rating Distribution
    # =====================
    rating_qs = (
        Review.objects
        .values("rating")
        .annotate(total=Count("id"))
        .order_by("rating")
    )

    return {
        # COUNTS
        "booking_count": Booking.objects.count(),
        "contact_count": ContactMessage.objects.count(),
        "hotel_count": Hotel.objects.count(),
        "room_count": Room.objects.count(),
        "review_count": Review.objects.count(),
        "nearby_count": NearbyPlace.objects.count(),

        # REVENUE
        "revenue_total": float(total_revenue),
        "revenue_labels": [
            r["month"].strftime("%b %Y") for r in revenue_qs if r["month"]
        ],
        "revenue_data": [
            float(r["total"]) for r in revenue_qs
        ],

        # RATINGS
        "rating_labels": [f'{r["rating"]} Star' for r in rating_qs],
        "rating_data": [r["total"] for r in rating_qs],
    }

def admin_dashboard_stats(request):
    return {
        "booking_count": Booking.objects.count(),
        "hotel_count": Hotel.objects.count(),
        "room_count": Room.objects.count(),
        "review_count": Review.objects.count(),
        "contact_count": ContactMessage.objects.count(),
        "revenue_total": sum(
            Booking.objects.filter(is_paid=True).values_list("total_amount", flat=True)
        )
    }