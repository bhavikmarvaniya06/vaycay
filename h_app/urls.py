from django.urls import path
from . import views

urlpatterns = [

    # =========================
    # Home & Listings
    # =========================
    path('', views.home, name='home'),
    path('hotel/<int:id>/', views.hotel_detail, name='hotel_detail'),
    path('rooms/', views.rooms_page, name='rooms'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about, name='about'),
    path('search/', views.live_search, name='live_search'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),

    # =========================
    # Wishlist System
    # =========================
    path('wishlist/<int:hotel_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('my-wishlist/', views.my_wishlist, name='my_wishlist'),
    path('wishlist/clear/', views.clear_wishlist, name='clear_wishlist'),
    path('wishlist/share/<str:username>/', views.share_wishlist, name='share_wishlist'),

    # =========================
    # AJAX Filters
    # =========================
    path('ajax/filter-hotels/', views.ajax_filter_hotels, name='ajax_filter_hotels'),
    path('filter-hotels/', views.filter_hotels, name='filter_hotels'),

    # =========================
    # Authentication
    # =========================
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # =========================
    # Forgot Password OTP Flow
    # =========================
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('forgot/verify/', views.verify_reset_otp, name='verify_reset_otp'),
    path('forgot/new-password/', views.reset_new_password, name='reset_new_password'),

    # =========================
    # User Profile
    # =========================
    path('profile/', views.profile_view, name='profile'),
    path('profile/update/', views.profile_update, name='profile_update'),

    # =========================
    # Booking Flow
    # =========================
    path('book/<int:room_id>/', views.book_room, name='book_room'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('cancel-booking/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),

    # =========================
    # Invoice
    # =========================
    path('invoice/<int:booking_id>/', views.invoice_pdf, name='invoice_pdf'),

    # =========================
    # Payment
    # =========================
    path('payment/<int:booking_id>/', views.payment_page, name='payment_page'),
    path('payment-success/<int:booking_id>/', views.payment_success, name='payment_success'),

    # 🎁 SPIN + COUPON
    path('spin/', views.spin_discount, name='spin_discount'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('create-order/', views.create_order, name='create_order'),
]
