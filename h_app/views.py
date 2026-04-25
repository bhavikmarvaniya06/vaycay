from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
import razorpay
import random
from datetime import datetime,date
from decimal import Decimal
from django.urls import reverse
from django.template.loader import render_to_string
from .models import Hotel, Room, Booking, ContactMessage, Review, Wishlist, UserProfile
from .utils import generate_invoice_pdf, send_email_with_invoice
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from datetime import timedelta
from django.utils import timezone
import string
from .models import Coupon,Payment
from django.db import transaction





# =========================
# Home Page
# =========================
def home(request):
    category = request.GET.get('category')
    city = request.GET.get('city')
    brand = request.GET.get('brand')   # Taj, ITC, Oberoi
    
    hotels = Hotel.objects.all()

    if category:
        hotels = hotels.filter(category=category)

    if city:
        hotels = hotels.filter(city__iexact=city)

    # ✅ BRAND FILTER USING EXISTING FIELD
    if brand:
        hotels = hotels.filter(
            Q(also_known_as__icontains=brand) |
            Q(name__icontains=brand)
        )

    # ⭐ Reviews + pricing
    for hotel in hotels:
        reviews = Review.objects.filter(room__hotel=hotel)
        hotel.review_count = reviews.count()
        hotel.avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

        rooms = hotel.rooms.all()
        if rooms.exists():
            final_prices = [r.final_price for r in rooms]
            original_prices = [r.price for r in rooms]

            hotel.min_price = min(final_prices)
            hotel.min_original = min(original_prices)

            hotel.min_discount = (
                100 - int((hotel.min_price / hotel.min_original) * 100)
                if hotel.min_original > hotel.min_price else 0
            )
        else:
            hotel.min_price = hotel.min_original = hotel.min_discount = 0
            
            recommended = []

            if request.user.is_authenticated:
                wishlist_hotels = Hotel.objects.filter(wishlist__user=request.user)
                booked_hotels = Hotel.objects.filter(room__booking__user=request.user)

                user_hotels = wishlist_hotels | booked_hotels

                cities = user_hotels.values_list('city', flat=True)
                categories = user_hotels.values_list('category', flat=True)

                recommended = Hotel.objects.filter(
                    Q(city__in=cities) | Q(category__in=categories)
                ).exclude(
                    id__in=user_hotels.values_list('id', flat=True)
                ).distinct()[:6]

    # ❤️ Only 4⭐ & 5⭐ reviews
    top_reviews = Review.objects.filter(
        rating__in=[4, 5]
    ).select_related(
        'user', 'room', 'room__hotel'
    ).order_by('-created_at')[:3]

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('hotel_id', flat=True)

    POPULAR_CITIES = [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai",
        "Kolkata", "Pune", "Ahmedabad", "Surat", "Jaipur", "Goa"
    ]

    return render(request, 'home.html', {
        'hotels': hotels,
        'wishlist_ids': wishlist_ids,
        'selected_category': category,
        'selected_city': city,
        'selected_brand': brand,
        'popular_cities': POPULAR_CITIES,
        'top_reviews': top_reviews,
    })


# =========================
# Rooms Page
# =========================
def rooms_page(request):
    category = request.GET.get('category')

    # ✅ REMOVE prefetch_related (MAIN FIX)
    rooms = Room.objects.select_related('hotel').all()

    if category:
        rooms = rooms.filter(hotel__category=category)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    view_type = request.GET.get('view_type')
    available = request.GET.get('available')

    if min_price:
        rooms = rooms.filter(price__gte=min_price)

    if max_price:
        rooms = rooms.filter(price__lte=max_price)

    if view_type:
        rooms = rooms.filter(view_type=view_type)

    if available:
        rooms = rooms.filter(is_available=True)

    # ✅ ROOM COUNT (SAME)
    room_counts = (
        Room.objects
        .filter(is_available=True)
        .values('room_name')
        .annotate(total=Count('id'))
    )

    context = {
        'rooms': rooms,
        'views': Room.VIEW_TYPE,
        'selected_category': category,
        'room_counts': room_counts
    }

    return render(request, 'rooms.html', context)

# =========================
# Hotel Detail
# =========================
def hotel_detail(request, id):
    hotel = get_object_or_404(Hotel, id=id)
    rooms = hotel.rooms.all()
    nearby = hotel.nearby.all()

    return render(request, 'hotel_detail.html', {
        'hotel': hotel,
        'rooms': rooms,
        'nearby': nearby
    })


# =========================
# Login
# =========================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('/admin/' if request.user.is_staff else 'home')

    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user:
            login(request, user)

            # 📧 EMAIL ON LOGIN
            if user.email:
                send_mail(
    subject="New Login Alert 🔐",
    message=f"""
Hello {user.username},

Your account was just logged in successfully.

If this was not you, please change your password.
""",
    from_email=settings.DEFAULT_FROM_EMAIL,
    recipient_list=[user.email],
    fail_silently=False,   # ✅ IMPORTANT
)


            return redirect('/admin/' if user.is_staff else 'home')

        messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')

# =========================
# Register
# =========================
def register_view(request):

    # 🔒 Already logged in → home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # ❌ Empty fields
        if not username or not email or not password1 or not password2:
            messages.error(request, "All fields are required!")
            return redirect('register')

        # ❌ Password mismatch
        if password1 != password2:
            messages.error(request, "Passwords do not match!")
            return redirect('register')

        # ❌ Username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('register')

        # ❌ Email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        # ✅ Create user
        User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        # 📧 Email (optional)
        try:
            if email:
                send_mail(
                    subject="Welcome to Hotel Management System 🎉",
                    message=f"""
Hello {username},

Your account has been created successfully.

You can now login.

Regards,
Hotel Team
""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=True,  # ⚠️ better to avoid crash
                )
        except Exception as e:
            print("Email error:", e)

        # ✅ Success message
        messages.success(request, "Registration successful! Please login.")

        # 🔥 DIRECT redirect to login
        return redirect('login')

    return render(request, 'register.html')
# =========================
# Logout
# =========================
def logout_view(request):
    logout(request)
    return redirect('login')


# =========================
# Book Room
# =========================
@login_required(login_url='login')
def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)

    # 🔥 Today date (for HTML min)
    today = date.today()

    if request.method == 'POST':
        try:
            check_in = datetime.strptime(request.POST['check_in'], "%Y-%m-%d").date()
            check_out = datetime.strptime(request.POST['check_out'], "%Y-%m-%d").date()
        except:
            messages.error(request, "Invalid date format")
            return redirect('book_room', room_id=room.id)

        # ❌ PAST DATE BLOCK
        if check_in < today:
            messages.error(request, "Check-in date cannot be in the past")
            return redirect('book_room', room_id=room.id)

        # ❌ WRONG DATE
        if check_out <= check_in:
            messages.error(request, "Check-out must be after check-in")
            return redirect('book_room', room_id=room.id)

        # ❌ ROOM NOT AVAILABLE
        if room.quantity <= 0:
            messages.error(request, "Room not available")
            return redirect('rooms_page')

        # ✅ CALCULATIONS
        total_nights = (check_out - check_in).days
        base_amount = Decimal(total_nights) * room.price

        # ✅ CREATE BOOKING
        booking = Booking.objects.create(
            user=request.user,
            room=room,
            name=request.POST['name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            country=request.POST['country'],
            check_in=check_in,
            check_out=check_out,
            adults=request.POST['adults'],
            children=request.POST['children'],
            total_nights=total_nights,
            base_amount=base_amount,
            gst_percent=room.hotel.gst_percent,
            status='pending',
            is_paid=False
        )

        return redirect('payment_page', booking.id)

    return render(request, 'book_room.html', {
        'room': room,
        'today': today.isoformat()   # 🔥 important for HTML
    })

# =========================
# Razorpay Payment (WITH DISCOUNT)
# =========================
@login_required(login_url='login')
def payment_page(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.is_paid:
        return redirect('my_bookings')

    # 🎟 coupon logic
    coupon = Coupon.objects.filter(user=request.user, is_used=False).first()

    final_amount = booking.final_amount  
    discount_amount = 0

    if coupon and coupon.expires_at > timezone.now():
        discount_amount = (booking.base_amount * coupon.discount) / 100
        final_amount = booking.final_amount   - discount_amount

    # 💳 Razorpay
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    amount = int(final_amount * 100)

    order = client.order.create({
        'amount': amount,
        'currency': 'INR',
        'payment_capture': 1
    })

    booking.razorpay_order_id = order['id']
    booking.save(update_fields=['razorpay_order_id'])

    # ✅ THIS RETURN MUST BE INSIDE FUNCTION
    return render(request, 'payment.html', {
        'booking': booking,
        'order': order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'amount': amount,
        'final_amount': final_amount,
        'discount_amount': discount_amount,
        'coupon': coupon
    })
#@login_required(login_url='login')
def payment_success(request, booking_id):

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.is_paid:
        return redirect('my_bookings')

    import razorpay
    from django.conf import settings
    from decimal import Decimal

    # ✅ POST DATA
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')
    razorpay_order_id = request.POST.get('razorpay_order_id')

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    payment_method = "unknown"

    # ✅ VERIFY SIGNATURE
    try:
        if razorpay_payment_id and razorpay_signature:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)

    except Exception as e:
        print("Signature error:", e)
        messages.error(request, "Payment verification failed")
        return redirect('my_bookings')

    # ✅ FETCH PAYMENT METHOD
    try:
        if razorpay_payment_id:
            payment_data = client.payment.fetch(razorpay_payment_id)
            payment_method = payment_data.get("method", "unknown")

    except Exception as e:
        print("Fetch error:", e)

    # ===============================
    # ✅ GET FINAL AMOUNT FROM FRONTEND
    # ===============================
    final_amount = request.POST.get('final_amount')

    if final_amount:
        final_amount = Decimal(final_amount)
        discount_amount = booking.final_amount   - final_amount
    else:
        final_amount = booking.final_amount  
        discount_amount = Decimal("0.00")

    # ✅ SAVE BOOKING
    booking.discount_amount = discount_amount
    booking.final_amount = final_amount
    booking.is_paid = True
    booking.status = 'confirmed'
    booking.save()

    # ✅ SAVE PAYMENT
    Payment.objects.create(
        booking=booking,
        customer_name=booking.name,
        email=booking.email,
        razorpay_order_id=razorpay_order_id or "test_order_id",
        razorpay_payment_id=razorpay_payment_id or "test_payment_id",
        razorpay_signature=razorpay_signature or "test_signature",
        amount=final_amount,
        status="Success",
        payment_method=payment_method
    )

    # ✅ UPDATE ROOM
    with transaction.atomic():
        room = Room.objects.select_for_update().get(id=booking.room.id)

        if room.quantity > 0:
            room.quantity -= 1
            room.save()
        else:
            messages.error(request, "Room not available")
            return redirect('rooms_page')

    # ✅ EMAIL
    subject = "Booking Confirmed – GST Invoice"
    message = f"""
Hello {booking.name},

Your booking is confirmed.

Hotel: {booking.room.hotel.name}
Room: {booking.room.room_name}

Base Amount: ₹{booking.base_amount}
GST ({booking.gst_percent}%): ₹{booking.gst_amount}
Discount: ₹{booking.discount_amount}
Total Paid: ₹{booking.final_amount}

Invoice is attached.
"""

    send_email_with_invoice(subject, message, booking)

    messages.success(request, "Payment successful! GST Invoice sent to email.")
    return redirect('my_bookings')
# =========================
# My Bookings
# =========================
@login_required(login_url='login')
def my_bookings(request):
    bookings = Booking.objects.select_related(
        'room', 'room__hotel'
    ).filter(user=request.user).order_by('-booked_on')

    return render(request, 'my_bookings.html', {'bookings': bookings})


# =========================
# Booking Detail
# =========================
@login_required(login_url='login')
def booking_detail(request, booking_id):
    booking = get_object_or_404(
        Booking, id=booking_id, user=request.user
    )
    return render(request, 'booking_detail.html', {'booking': booking})


# =========================
# Cancel Booking
# =========================
@login_required(login_url='login')
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if booking.status == 'cancelled':
        messages.info(request, 'Booking already cancelled.')
        return redirect('my_bookings')

    booking.status = 'cancelled'
    booking.is_paid = False
    booking.save()

    room = booking.room
    room.quantity += 1
    room.save()

    send_mail(
        "Booking Cancelled",
        f"Hello {booking.name},\n\nYour booking has been cancelled.",
        settings.DEFAULT_FROM_EMAIL,
        [booking.email],
        fail_silently=False
    )

    messages.success(request, 'Booking cancelled and email sent.')
    return redirect('my_bookings')


# =========================
# Invoice Download
# =========================
@login_required(login_url='login')
def invoice_pdf(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    pdf = generate_invoice_pdf(booking)

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="invoice_{booking.id}.pdf"'
    )
    return response


# =========================
# Contact page
# =========================
def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # ✅ Save message to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # ✅ Send email to USER
        send_mail(
            subject="We received your message ✔",
            message=f"""
Hello {name},

Thank you for contacting Hotel Management System.

We have received your message:

Subject: {subject}
Message:
{message}

Our support team will get back to you shortly.

Regards,
Hotel Management Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],   # 👈 USER EMAIL
            fail_silently=False,
        )

        # ✅ Success message on website
        messages.success(request, "Your message has been sent successfully! Please check your email.")

        return redirect('contact')

    return render(request, 'contact.html')

# =========================
# About page
# =========================
def about(request):
    return render(request, 'about.html')


# =========================
# Search bar
# =========================
def live_search(request):
    query = request.GET.get('q', '')

    hotels = Hotel.objects.filter(
        name__icontains=query
    ).values('id', 'name')

    rooms = Room.objects.select_related('hotel').filter(
        Q(room_name__icontains=query) |
        Q(view_type__icontains=query) |
        Q(hotel__name__icontains=query)
    ).values(
        'id', 'room_name', 'view_type', 'hotel__name'
    )

    return JsonResponse({
        'hotels': list(hotels),
        'rooms': list(rooms)
    })


# =========================
# Review page
# =========================
@login_required(login_url='login')
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    reviews = room.reviews.all()

    if request.method == 'POST':
        Review.objects.create(
            user=request.user,
            room=room,
            rating=request.POST['rating'],
            comment=request.POST['comment']
        )
        messages.success(request, 'Review added successfully!')
        return redirect('room_detail', room_id=room.id)

    return render(request, 'room_detail.html', {
        'room': room,
        'reviews': reviews
    })


# =========================
# toggle_wishlist page
# =========================
@login_required(login_url='login')
def toggle_wishlist(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user,
        hotel=hotel
    )

    if created:
        return JsonResponse({'status': 'added'})
    else:
        wishlist.delete()
        return JsonResponse({'status': 'removed'})


# =========================
# my_wishlist page
# =========================
@login_required(login_url='login')
def my_wishlist(request):
    hotels = Hotel.objects.filter(wishlist__user=request.user)

    share_url = request.build_absolute_uri(
        reverse('share_wishlist', args=[request.user.username])
    )

    return render(request, 'wishlist.html', {
        'hotels': hotels,
        'share_url': share_url
    })


# =========================
# share_wishlist page (PUBLIC)
# =========================
def share_wishlist(request, username):
    user = get_object_or_404(User, username=username)

    hotels = Hotel.objects.filter(wishlist__user=user)

    return render(request, 'share_wishlist.html', {
        'shared_user': user,
        'hotels': hotels
    })


# =========================
# clear_wishlist page
# =========================
@login_required(login_url='login')
def clear_wishlist(request):
    if request.method == "POST":
        Wishlist.objects.filter(user=request.user).delete()
        return JsonResponse({'status': 'cleared'})


def ajax_filter_hotels(request):
    category = request.GET.get('category')
    city = request.GET.get('city')
    brand = request.GET.get('brand')

    hotels = Hotel.objects.all()

    if category:
        hotels = hotels.filter(category=category)

    if city:
        hotels = hotels.filter(city__iexact=city)

    if brand:
        hotels = hotels.filter(
            Q(name__icontains=brand) |
            Q(also_known_as__icontains=brand)
        )

    # ratings
    for hotel in hotels:
        reviews = Review.objects.filter(room__hotel=hotel)
        hotel.review_count = reviews.count()
        hotel.avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(
            user=request.user
        ).values_list('hotel_id', flat=True)

    html = render_to_string(
        'partials/hotel_cards.html',
        {'hotels': hotels, 'wishlist_ids': wishlist_ids},
        request=request
    )

    return JsonResponse({'html': html})


def filter_hotels(request):
    category = request.GET.get('category')
    city = request.GET.get('city')

    hotels = Hotel.objects.all()

    if category:
        hotels = hotels.filter(category=category)

    if city:
        hotels = hotels.filter(city__iexact=city)

    for hotel in hotels:
        reviews = Review.objects.filter(room__hotel=hotel)
        hotel.review_count = reviews.count()
        hotel.avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('hotel_id', flat=True)

    html = render_to_string('partials/hotels_list.html', {
        'hotels': hotels,
        'wishlist_ids': wishlist_ids,
    }, request=request)

    return JsonResponse({'html': html})


@login_required(login_url='login')
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    bookings = Booking.objects.filter(user=request.user).order_by('-booked_on')
    wishlist = Wishlist.objects.filter(user=request.user).select_related('hotel')

    return render(request, 'profile.html', {
        'profile': profile,
        'bookings': bookings,
        'wishlist': wishlist,
    })


@login_required(login_url='login')
def profile_update(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # Update base user
        request.user.username = request.POST['username']
        request.user.email = request.POST['email']
        request.user.save()

        # Update profile
        profile.phone = request.POST.get('phone')
        profile.city = request.POST.get('city')
        profile.country = request.POST.get('country')
        profile.address = request.POST.get('address')

        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('profile')

    return render(request, 'profile_update.html', {
        'profile': profile
    })


# =========================
# FORGOT PASSWORD with EMAIL OTP ONLY
# =========================

def forgot_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email.")
            return redirect('forgot_password')

        # <-- FIX HERE (no .get())
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No account found with this email!")
            return redirect('forgot_password')

        otp = random.randint(100000, 999999)

        request.session['reset_otp'] = str(otp)
        request.session['reset_user_id'] = user.id

        # SEND EMAIL OTP
        send_mail(
            subject="Password Reset OTP",
            message=f"Your OTP is: {otp}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False
        )

        messages.success(request, "OTP sent to your email!")
        return redirect('verify_reset_otp')

    return render(request, 'forgot_password.html')

def verify_reset_otp(request):
    if request.method == "POST":
        otp = request.POST.get("otp")

        if otp == request.session.get("reset_otp"):
            request.session['reset_verified'] = True
            return redirect('reset_new_password')

        messages.error(request, "Invalid OTP")
        return redirect('verify_reset_otp')

    return render(request, 'verify_reset_otp.html')


def reset_new_password(request):
    if not request.session.get('reset_verified'):
        messages.error(request, "Unauthorized Action")
        return redirect('forgot_password')

    if request.method == "POST":
        p1 = request.POST['password1']
        p2 = request.POST['password2']

        if p1 != p2:
            messages.error(request, "Passwords do not match!")
            return redirect('reset_new_password')

        user = User.objects.get(id=request.session.get('reset_user_id'))
        user.set_password(p1)
        user.save()

        request.session.flush()

        messages.success(request, "Password Reset Successfully! Login Now.")
        return redirect('login')

    return render(request, 'reset_new_password.html')

@login_required
def spin_discount(request):

    # 🔥 only count unused coupons (important)
    spin_count = Coupon.objects.filter(user=request.user, is_used=False).count()

    # ❌ max 2 spins
    if spin_count >= 2:
        return JsonResponse({
            'status': 'limit',
            'message': 'You can only spin 2 times'
        })

    # 🎯 random discount
    discount = random.choice([5, 10, 15, 20])

    # 🎟️ unique coupon code
    while True:
        code = "HOTEL" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        if not Coupon.objects.filter(code=code).exists():
            break

    expiry = timezone.now() + timedelta(days=1)

    coupon = Coupon.objects.create(
        user=request.user,
        code=code,
        discount=discount,
        expires_at=expiry
    )

    return JsonResponse({
        'status': 'new',
        'code': coupon.code,
        'discount': coupon.discount,
        'spins_left': 2 - (spin_count + 1)
    })
    
@login_required(login_url='login')
def apply_coupon(request):

    code = request.GET.get('code', '').strip()

    if not code:
        return JsonResponse({'valid': False, 'error': 'Enter coupon code'})

    try:
        coupon = Coupon.objects.get(code=code, user=request.user)

        if coupon.is_used:
            return JsonResponse({'valid': False, 'error': 'Coupon already used'})

        if coupon.expires_at < timezone.now():
            return JsonResponse({'valid': False, 'error': 'Coupon expired'})

        # ✅ STORE IN SESSION
        request.session['coupon_id'] = coupon.id

        return JsonResponse({
            'valid': True,
            'discount': coupon.discount,
            'code': coupon.code
        })

    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Invalid coupon'})
    
@login_required
def create_order(request):

    amount = request.GET.get('amount')

    if not amount:
        return JsonResponse({'error': 'Invalid amount'})

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    order = client.order.create({
        'amount': int(float(amount) * 100),
        'currency': 'INR',
        'payment_capture': 1
    })

    return JsonResponse({
        'order_id': order['id']
    })