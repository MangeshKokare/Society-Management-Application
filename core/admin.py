from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Apartment,
    UserProfile,
    Visitor,
    Delivery,
    Service,
    DailyHelp,
    EmergencyContact,
    Announcement,
    CommunityPost,
    Poll,
    PollOption
)

# =========================
# USER PROFILE INLINE (Phone + Apartment inside User)
# =========================

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'


# =========================
# EXTEND DJANGO USER ADMIN
# =========================

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Unregister default User and re-register
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# =========================
# REGISTER OTHER MODELS
# =========================

@admin.register(Apartment)
class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('society', 'block', 'flat_number')
    search_fields = ('society_name', 'flat_number')


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'visitor_type', 'mobile', 'status', 'created_at')
    list_filter = ('visitor_type', 'status')
    search_fields = ('name', 'mobile')


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('company', 'tracking_id', 'status', 'received_at')
    search_fields = ('company', 'tracking_id')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'active')
    list_filter = ('active',)


@admin.register(DailyHelp)
class DailyHelpAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'mobile', 'user', 'active')
    list_filter = ('service', 'active')
    search_fields = ('name', 'mobile')


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = ('title', 'phone')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    search_fields = ('title',)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'apartment', 'likes', 'comments', 'created_at')
    search_fields = ('user__username', 'apartment')


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 2


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'created_by', 'created_at')
    inlines = [PollOptionInline]

from django.contrib import admin
from .models import ServiceProvider, HiredService, ServiceReview

@admin.register(ServiceProvider)
class ServiceProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'area', 'city', 'verification_status', 'rating', 'is_available']
    list_filter = ['service', 'verification_status', 'city', 'is_available']
    search_fields = ['name', 'mobile', 'area']
    
@admin.register(HiredService)
class HiredServiceAdmin(admin.ModelAdmin):
    list_display = ['resident', 'service_provider', 'status', 'monthly_payment', 'start_date']
    list_filter = ['status', 'start_date']
    
@admin.register(ServiceReview)
class ServiceReviewAdmin(admin.ModelAdmin):
    list_display = ['hired_service', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']