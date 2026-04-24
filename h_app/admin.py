from django.contrib import admin
from django.contrib.admin import site
from django.shortcuts import redirect
from django.urls import path
from django.db.models import Sum
from .models import (
    Hotel, HotelImage,
    Room, RoomImage,
    Booking,
    ContactMessage,
    Review,
    NearbyPlace,
    Payment
)
class BaseDeleteAdmin(admin.ModelAdmin):
    change_list_template = "admin/custom_delete.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'delete-selected/',
                self.admin_site.admin_view(self.delete_selected_view),
                name="delete_selected_custom"
            ),
        ]
        return custom_urls + urls

    def delete_selected_view(self, request):
        if request.method == "POST":

            # 🔥 get ids (string format: "5,4,3,2")
            ids = request.POST.get("ids", "")

            # 🔥 convert to integer list
            id_list = [int(i) for i in ids.split(",") if i.isdigit()]

            # ❌ no selection
            if not id_list:
                self.message_user(request, "No records selected ❌")
                return redirect(request.META.get('HTTP_REFERER'))

            queryset = self.model.objects.filter(id__in=id_list)
            count = queryset.count()

            queryset.delete()

            self.message_user(request, f"{count} records deleted successfully ✅")

        return redirect(request.META.get('HTTP_REFERER'))
# =====================================================
# 🔢 ADD COUNTS TO ADMIN DASHBOARD (SAFE METHOD)
# =====================================================
_original_index = site.index

def custom_admin_index(request, extra_context=None):
    if extra_context is None:
        extra_context = {}

    extra_context.update({
        "hotel_count": Hotel.objects.count(),
        "room_count": Room.objects.count(),
        "booking_count": Booking.objects.count(),
        "review_count": Review.objects.count(),
    })

    return _original_index(request, extra_context)

site.index = custom_admin_index


admin.site.site_header = "Hotel Management Admin"
admin.site.site_title = "Hotel Management"
admin.site.index_title = "Dashboard Overview"


# =========================
# Hotel Image Inline
# =========================
class HotelImageInline(admin.TabularInline):
    model = HotelImage
    extra = 3


# =========================
# Room Image Inline
# =========================
class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 3


# =========================
# Room Inline (Under Hotel)
# =========================
class RoomInline(admin.TabularInline):
    model = Room
    extra = 2
    fields = (
        'room_number',
        'room_name',
        'view_type',
        'price',
        'discount',
        'quantity',
        'is_available'
    )
    show_change_link = True


# =========================
# Hotel Admin
# =========================
@admin.register(Hotel)
class HotelAdmin(BaseDeleteAdmin):   

    list_display = (
        'name',
        'category',
        'gst_number',
        'gst_percent',
        'total_rooms',        # ✅ add
        'available_rooms'     # ✅ add
    )

    search_fields = ('name', 'gst_number', 'category')
    list_filter = ('category',)
    inlines = [HotelImageInline, RoomInline]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'description', 'category',
                'city', 'address', 'price',
                'discount', 'rating'
            )
        }),
        ('At a Glance', {
            'fields': (
                'hotel_size', 'check_in_time',
                'check_out_time', 'min_check_in_age',
                'special_checkin_info'
            )
        }),
        ('Amenities', {
            'fields': (
                'has_pool', 'has_spa', 'has_wifi',
                'has_restaurant', 'has_parking',
                'has_breakfast', 'pets_allowed',
                'smoking_area'
            )
        }),
        ('GST Details', {
            'fields': ('gst_number', 'gst_percent')
        }),
        ('Fees & Policies', {
            'fields': (
                'refundable_deposit',
                'breakfast_price_adult',
                'breakfast_price_child',
                'pool_timings',
                'policies',
                'also_known_as'
            )
        }),
    )

    # 🔥 MUST BE INSIDE CLASS
    def total_rooms(self, obj):
        return obj.rooms.aggregate(total=Sum('quantity'))['total'] or 0

    def available_rooms(self, obj):
        return obj.rooms.filter(is_available=True).aggregate(
            total=Sum('quantity')
        )['total'] or 0


# =========================
# Room Admin
# =========================
@admin.register(Room)
class RoomAdmin(BaseDeleteAdmin):
    list_display = (
        'room_number',
        'hotel',
        'get_category',
        'room_name',
        'view_type',
        'price',
        'discount',
        'final_price',
        'quantity',
        'is_available',
    )
    list_filter = (
        'hotel__category',
        'view_type',
        'is_available',
    )
    search_fields = ('room_number', 'hotel__name')
    inlines = [RoomImageInline]

    @admin.display(description="Category")
    def get_category(self, obj):
        return obj.hotel.get_category_display()


# =========================
# Booking Admin
# =========================
@admin.register(Booking)
class BookingAdmin(BaseDeleteAdmin):
    list_display = (
        'id',
        'user',
        'room',
        'status',
        'is_paid',
        'check_in',
        'check_out',
        'booked_on'
    )
    list_filter = (
        'status',
        'is_paid',
        'check_in',
        'check_out'
    )
    search_fields = (
        'user__username',
        'name',
        'email',
        'room__hotel__name'
    )
    list_editable = ('status', 'is_paid')
    ordering = ('-booked_on',)
    readonly_fields = ('booked_on',)


# =========================
# Contact Message Admin
# =========================
@admin.register(ContactMessage)
class ContactMessageAdmin(BaseDeleteAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    search_fields = ('name', 'email', 'subject')
    readonly_fields = ('created_at',)


# =========================
# Review Admin
# =========================
@admin.register(Review)
class ReviewAdmin(BaseDeleteAdmin):
    list_display = ('room', 'user', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('room__room_name', 'user__username')


# =========================
# Nearby Place Admin
# =========================
@admin.register(NearbyPlace)
class NearbyPlaceAdmin(BaseDeleteAdmin):
    list_display = ('title', 'hotel', 'time', 'distance')
    search_fields = ('title', 'hotel__name')


# =========================
#  Payment Admin
# =========================
@admin.register(Payment)
class PaymentAdmin(BaseDeleteAdmin):
    list_display = (
        'id',
        'customer_name',
        'email',
        'amount',
        'payment_method',   
        'razorpay_payment_id',
        'status',
        'created_at'
    )

    search_fields = (
        'customer_name',
        'email',
        'razorpay_payment_id'
    )

    list_filter = ('status', 'created_at')

    ordering = ('-created_at',)