from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Avg
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid

# =========================
# Hotel Model
# =========================
class Hotel(models.Model):
    CATEGORY_CHOICES = (
        ('hotel', 'Hotel'),
        ('villa', 'Villa'),
        ('resort', 'Resort'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='hotel')

    city = models.CharField(max_length=100, default='Unknown')
    address = models.CharField(max_length=255, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)

    has_pool = models.BooleanField(default=True)
    has_spa = models.BooleanField(default=True)
    has_wifi = models.BooleanField(default=True)
    has_restaurant = models.BooleanField(default=True)
    has_parking = models.BooleanField(default=True)
    has_breakfast = models.BooleanField(default=True)

    hotel_size = models.PositiveIntegerField(default=0)
    check_in_time = models.CharField(max_length=50, default="2:00 PM")
    check_out_time = models.CharField(max_length=50, default="12:00 PM")
    min_check_in_age = models.PositiveIntegerField(default=18)
    special_checkin_info = models.TextField(blank=True)

    require_id = models.BooleanField(default=True)
    require_deposit = models.BooleanField(default=True)
    pets_allowed = models.BooleanField(default=False)

    wifi_speed = models.CharField(max_length=50, default="25+ Mbps")
    free_self_parking = models.BooleanField(default=True)
    free_valet_parking = models.BooleanField(default=True)
    smoking_area = models.BooleanField(default=True)

    refundable_deposit = models.PositiveIntegerField(default=2000)
    breakfast_price_adult = models.PositiveIntegerField(default=499)
    breakfast_price_child = models.PositiveIntegerField(default=349)
    pool_timings = models.CharField(max_length=100, default="6:00 AM – 6:00 PM")
    policies = models.TextField(blank=True)
    also_known_as = models.CharField(max_length=200, blank=True)

    gst_number = models.CharField(max_length=20, blank=True)
    gst_percent = models.PositiveIntegerField(default=18)

    def __str__(self):
        return f"{self.name} - {self.city}"

    @property
    def final_price(self):
        if self.discount > 0:
            return self.price - (self.price * self.discount / 100)
        return self.price


# =========================
# Hotel Images
# =========================
class HotelImage(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='hotel_images/')

    def __str__(self):
        return f"Image of {self.hotel.name}"


# =========================
# Room Model (with Discount)
# =========================
class Room(models.Model):

    ROOM_NAME = [
        ('Superior Twin', 'Superior Twin Room'),
        ('Premium', 'Premium Room'),
        ('Executive', 'Executive Room'),
        ('Deluxe', 'Deluxe Room'),
        ('Suite', 'Suite Room'),
    ]

    VIEW_TYPE = [
        ('City', 'City View'),
        ('River', 'River View'),
        ('Mountain', 'Mountain View'),
        ('Garden', 'Garden View'),
        ('Sea', 'Sea View'),
    ]

    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE, related_name='rooms')

    room_number = models.IntegerField()
    room_name = models.CharField(max_length=30, choices=ROOM_NAME)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    discount = models.PositiveIntegerField(default=0)

    size_sq_m = models.PositiveIntegerField(default=20)
    sleeps = models.PositiveIntegerField(default=2)
    view_type = models.CharField(max_length=20, choices=VIEW_TYPE, default='City')

    has_wifi = models.BooleanField(default=True)
    refundable = models.BooleanField(default=True)

    # 🔥 MAIN STOCK SYSTEM
    quantity = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['room_number']
        unique_together = ('hotel', 'room_number')

    def __str__(self):
        return f"{self.hotel.name} - {self.room_name} ({self.view_type})"

    # 🔥 AUTO availability (CORE LOGIC)
    def save(self, *args, **kwargs):
        self.is_available = self.quantity > 0
        super().save(*args, **kwargs)

    # ⭐ Reviews
    @property
    def rating_count(self):
        return self.reviews.count()

    @property
    def average_rating(self):
        return self.reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    # 💰 Pricing
    @property
    def final_price(self):
        if self.discount > 0:
            return self.price - (self.price * self.discount / 100)
        return self.price

    @property
    def savings(self):
        return self.price - self.final_price

    # 🔥 EXTRA (UI use)
    @property
    def is_low_stock(self):
        return self.quantity <= 2

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "Sold Out"
        elif self.quantity <= 2:
            return "Only few left"
        return "Available"
    
# =========================
# Room Images
# =========================
class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='room_images/')

    def __str__(self):
        return f"Image of {self.room}"


# =========================
# Booking Model
# =========================
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey('Room', on_delete=models.CASCADE, related_name='bookings')

    # Customer Info
    name = models.CharField(max_length=100, default='-')
    email = models.EmailField(default='-')
    phone = models.CharField(max_length=20, default='-')
    address = models.TextField(default='-')
    country = models.CharField(max_length=50, default='-')

    # Booking Details
    check_in = models.DateField()
    check_out = models.DateField()
    total_nights = models.PositiveIntegerField(default=1)

    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)

    # 💰 Pricing
    base_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    gst_percent = models.PositiveIntegerField(default=18)
    gst_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # 👉 MAIN FINAL FIELD (use this everywhere)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # Payment Info
    is_paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booked_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.room} - ₹{self.total_amount}"

    # 🔥 SAFE PROPERTY (old code compatibility)
    @property
    def amount(self):
        return self.total_amount
    class Meta:
        ordering = ['-booked_on']

    def save(self, *args, **kwargs):
        self.gst_amount = (Decimal(self.base_amount) * Decimal(self.gst_percent) / Decimal("100"))
        self.total_amount = Decimal(self.base_amount) + Decimal(self.gst_amount)

        # 🔥 FINAL AMOUNT CALCULATION
        if self.discount_amount > 0:
            self.total_amount = self.total_amount - self.discount_amount
        else:
            self.total_amount = self.total_amount

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} | {self.room} | {self.status}"
# =========================
# Contact
# =========================
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"


# =========================
# Review
# =========================
class Review(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.rating}⭐"


# =========================
# Wishlist
# =========================
class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'hotel')

    def __str__(self):
        return f"{self.user} - {self.hotel}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    
class NearbyPlace(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="nearby")
    title = models.CharField(max_length=200)
    time = models.CharField(max_length=50)   # e.g. "2 min drive"
    icon = models.CharField(max_length=50, blank=True, null=True)  # optional
    distance = models.CharField(max_length=50, blank=True, null=True)  # optional

    def __str__(self):
        return self.title


class Coupon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=20, unique=True)
    discount = models.IntegerField()  # % discount
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.code} - {self.discount}%"
    

class Payment(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")

    customer_name = models.CharField(max_length=100)
    email = models.EmailField()
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    razorpay_order_id = models.CharField(max_length=200)
    razorpay_payment_id = models.CharField(max_length=200)
    razorpay_signature = models.CharField(max_length=200)

    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default="Success")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer_name} - {self.amount}"