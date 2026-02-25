from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import timedelta
from django.db.models import Count
from .models import ServiceReview
from django.http import HttpResponse
import csv
from datetime import date
from django.views.decorators.http import require_POST
import json
import traceback
from zoneinfo import ZoneInfo 
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import CommunityPost, Announcement, Poll, PollOption
from .decorators import role_required
from django.utils import timezone
import pytz
from .forms import UserUpdateForm, UserProfileForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import (
    EmergencyAlert,
    Notification,
    DailyHelpAttendance,
    EmergencyContact,
    Vehicle,
    HiredService,
)
from .models import (
    Apartment,
    Visitor,
    UserProfile,
    Announcement,
    DailyHelp,
    Service,
    CommunityPost,
    Poll,
    Delivery,
    Complaint,
    Society,
    PostLike,
    Comment,
    VisitorPhoto,
    IncidentReport,
    PatrolRound,
    Checkpoint,
    CheckpointScan,
    GuardShift,
    LeaveRequest,
    GuardAdminChat,
)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import F
from .models import (
    CommunityPost, Announcement, Poll, PollOption, PollVote,
    UserProfile, Society, Apartment
)
import json

from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from collections import Counter
from django.utils.timezone import now
from .decorators import role_required

# ---------------- HOME ----------------
@login_required(login_url='login')
def home(request):
    profile = request.user.userprofile
    apartment = profile.apartment

    recent_visitors = Visitor.objects.order_by('-created_at')[:3]
    announcements = Announcement.objects.order_by('-created_at')[:2]

    pending_count = Visitor.objects.filter(status='pending').count()

    return render(request, 'index.html', {
        'apartment': apartment,
        'recent_visitors': recent_visitors,
        'announcements': announcements,
        'pending_count': pending_count,
    })


# ---------------- VISITORS ----------------
@login_required(login_url='login')
def visitors(request):

    if request.method == 'POST':
        Visitor.objects.create(
            name=request.POST.get('name'),
            mobile=request.POST.get('mobile'),
            visitor_type=request.POST.get('visitor_type'),
            expected_at=request.POST.get('expected_at'),
            purpose=request.POST.get('purpose'),
            status='pending'
        )

    context = {
        'pending_visitors': Visitor.objects.filter(status='pending').order_by('-created_at'),
        'approved_visitors': Visitor.objects.filter(
            status__in=['approved', 'checked_in']
        ).order_by('-created_at'),
        'history_visitors': Visitor.objects.filter(
            status='checked_out'
        ).order_by('-created_at'),
    }

    return render(request, 'visitors.html', context)

# ---------------- DELIVERIES ----------------
@login_required(login_url='login')
def deliveries(request):
    return render(request, 'delivery.html')


@login_required(login_url='login')
def services(request):
    user = request.user

    # 1️⃣ Get all available service types (Maid, Driver, etc.)
    services = Service.objects.all()

    # 2️⃣ Get daily helpers for logged-in user only
    daily_helpers = (
        DailyHelp.objects
        .filter(user=user)
        .select_related('service')
    )

    # 3️⃣ Count helpers per service (FAST & TEMPLATE-FRIENDLY)
    helper_counts = Counter(
        daily_helpers.values_list('service_id', flat=True)
    )

    # 4️⃣ Pending visitors count (apartment-aware if available)
    try:
        apartment = user.userprofile.apartment
        pending_visitors_count = Visitor.objects.filter(
            status='pending'
        ).count()
        # 👉 If you later add apartment FK to Visitor,
        # filter here using apartment=apartment
    except:
        pending_visitors_count = 0

    # 5️⃣ Context sent to template
    context = {
        'services': services,
        'daily_helpers': daily_helpers,
        'helper_counts': helper_counts,
        'pending_visitors_count': pending_visitors_count,
    }

    return render(request, 'services.html', context)

@login_required
@require_POST
def toggle_daily_help(request, id):
    try:
        help_obj = DailyHelp.objects.get(id=id, user=request.user)
        help_obj.active = not help_obj.active
        help_obj.save()

        return JsonResponse({'active': help_obj.active})
    except DailyHelp.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


# ---------------- EMERGENCY ----------------
@login_required(login_url='login')
def emergency(request):
    return render(request, 'emergency.html')




# ---------------- PROFILE ----------------
from .forms import ProfileEditForm, UserEmailForm

@login_required(login_url='login')
def profile(request):

    profile = UserProfile.objects.select_related(
        'apartment', 'apartment__society'
    ).get(user=request.user)

    # -------- STATS (UNCHANGED) --------
    visitors_count = Visitor.objects.count()

    active_services_count = DailyHelp.objects.filter(
        user=request.user,
        active=True
    ).count()

    deliveries_count = Delivery.objects.count()

    posts_count = Post.objects.filter(
        user=request.user
    ).count() if 'Post' in globals() else 0

    pending_visitors_count = Visitor.objects.filter(
        status='pending'
    ).count()

    # -------- FORM HANDLING --------
    if request.method == "POST":
        profile_form = ProfileEditForm(
            request.POST, instance=profile
        )
        user_form = UserEmailForm(
            request.POST, instance=request.user
        )

        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            return redirect("profile")

    else:
        profile_form = ProfileEditForm(instance=profile)
        user_form = UserEmailForm(instance=request.user)

    context = {
        "profile": profile,

        # forms
        "profile_form": profile_form,
        "user_form": user_form,

        # stats
        "visitors_count": visitors_count,
        "active_services_count": active_services_count,
        "deliveries_count": deliveries_count,
        "posts_count": posts_count,
        "pending_visitors_count": pending_visitors_count,
    }

    return render(request, "profile.html", context)



# ---------------- COMMUNITY ----------------

# @login_required(login_url='login')
# def community(request):

#     posts = CommunityPost.objects.select_related('user').order_by('-created_at')
#     announcements = Announcement.objects.order_by('-created_at')
#     polls = Poll.objects.prefetch_related('options').order_by('-created_at')

#     pending_visitors_count = Visitor.objects.filter(status='pending').count()

#     context = {
#         'posts': posts,
#         'announcements': announcements,
#         'polls': polls,
#         'pending_visitors_count': pending_visitors_count
#     }

#     return render(request, 'community.html', context)


# ================= AUTH =================

from django.contrib import messages

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if not user:
            messages.error(request, "Invalid username or password")
            return redirect("login")

        try:
            profile = user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(
                request,
                "Your account setup is incomplete."
            )
            return redirect("login")

        login(request, user)

        # 🔥 SERVICE PROVIDER → DIRECT ACCESS
        if profile.role == "service_provider":
            return redirect("service_provider_dashboard")

        # ⏳ Others need approval
        if profile.status != "approved":
            messages.info(
                request,
                "Your account is pending approval."
            )
            return redirect("pending_approval")

        if profile.role == "resident":
            return redirect("resident_dashboard")
        elif profile.role in ["guard", "guard_admin"]:
            return redirect("guard_dashboard")

        elif profile.role == "society_admin":
            return redirect("society_admin_dashboard")
        elif profile.role == "admin":
            return redirect("admin_dashboard")

    return render(request, "login.html")



def pending_approval(request):
    return render(request, "pending_approval.html")

@login_required
@role_required("resident")
def resident_dashboard(request):

    user = request.user
    profile = user.userprofile
    apartment = request.user.userprofile.apartment
    today = now().date()

    pending_visitors = Visitor.objects.filter(
        apartment=apartment,
        status="pending"
    ).order_by("-created_at")

    today_visitors = Visitor.objects.filter(
        apartment=apartment,
        created_at__date=today
    )

    attendance_today = DailyHelpAttendance.objects.filter(
        daily_help__user=user,
        date=today,
        check_in__isnull=False
    )


    deliveries = Delivery.objects.filter(
        apartment=apartment,
        status__iexact="received"
    )

    overstays = Visitor.objects.filter(
        apartment=apartment,
        status="checked_in",
        created_at__lt=now() - timedelta(hours=3)
    )


    announcements = Announcement.objects.order_by("-created_at")[:5]

    recent_activity = Visitor.objects.filter(
        apartment=apartment
    ).order_by("-created_at")[:5]

    context = {
        "user": user,
        "apartment": apartment,

        "pending_visitors": pending_visitors,
        "pending_count": pending_visitors.count(),

        "today_visitors_count": today_visitors.count(),
        "active_staff_count": attendance_today.count(),
        "overstays": overstays,

        "deliveries_count": deliveries.count(),

        "announcements": announcements,
        "recent_activity": recent_activity,
    }

    return render(request, "resident_index.html", context)

from itertools import chain

@login_required
@role_required("resident")
def resident_visitors(request):
    profile = request.user.userprofile
    apartment = profile.apartment
    society = profile.society

    pending_visitors = Visitor.objects.filter(
        apartment=apartment,
        society=society,
        status="pending"
    )

    active_visitors = Visitor.objects.filter(
        apartment=apartment,
        society=society,
        status="checked_in"
    )

    preapproved_visitors = Visitor.objects.filter(
        apartment=apartment,
        society=society,
        status="approved"
    )

    history_visitors = Visitor.objects.filter(
        apartment=apartment,
        society=society,
        status="checked_out"
    )

    all_visitors = list(chain(
        pending_visitors,
        preapproved_visitors,
        active_visitors,
        history_visitors
    ))

    return render(request, "resident_visitors.html", {
        "pending_visitors": pending_visitors,
        "active_visitors": active_visitors,
        "preapproved_visitors": preapproved_visitors,
        "history_visitors": history_visitors,
        "all_visitors": all_visitors,   # ✅ ADD THIS
        "pending_count": pending_visitors.count(),
        "active_count": active_visitors.count(),
        "preapproved_count": preapproved_visitors.count(),
        "history_count": history_visitors.count(),
    })

@login_required
@role_required("resident")
@require_POST
def reply_to_notification(request, notification_id):
    try:
        notification = Notification.objects.select_related(
            "sender", "parent"
        ).get(id=notification_id, user=request.user)

        message = request.POST.get("message", "").strip()
        if not message:
            return JsonResponse({"success": False})

        # 🔥 Find ROOT notification
        root = notification
        while root.parent:
            root = root.parent

        guard_user = root.sender  # ✅ ORIGINAL guard

        Notification.objects.create(
            user=guard_user,          # ✅ GUARANTEED guard
            sender=request.user,      # resident
            parent=root,              # thread root
            title="💬 Reply from Resident",
            message=message
        )

        return JsonResponse({"success": True})

    except Notification.DoesNotExist:
        return JsonResponse({"success": False}, status=404)



import random

def generate_entry_code():
    """Generate unique 6-digit entry code"""
    while True:
        code = str(random.randint(100000, 999999))
        if not Visitor.objects.filter(entry_code=code).exists():
            return code

@login_required
@role_required("resident")
def preapprove_visitor(request):
    if request.method == "POST":
        profile = request.user.userprofile

        entry_code = generate_entry_code()

        visitor = Visitor.objects.create(
            name=request.POST["name"],
            mobile=request.POST["mobile"],
            visitor_type=request.POST.get("visitor_type", "guest"),
            purpose=request.POST.get("purpose", ""),
            expected_at=request.POST.get("expected_at"),
            apartment=profile.apartment,
            society=profile.society,
            status="approved",
            entry_code=entry_code,
        )

        # 📸 SAVE PHOTOS (MULTIPLE)
        for image in request.FILES.getlist("photos"):
            VisitorPhoto.objects.create(
                visitor=visitor,
                photo=image,
                taken_by=request.user
            )

        messages.success(
            request,
            f"✅ Visitor pre-approved! Entry Code: <b>{entry_code}</b>"
        )
        return redirect("resident_visitors")


@login_required
@role_required("resident")
def approve_visitor(request, id):
    try:
        visitor = Visitor.objects.get(
            id=id,
            apartment=request.user.userprofile.apartment,
            status="pending"
        )

        visitor.entry_code = generate_entry_code()
        visitor.status = "approved"  # approved, NOT checked_in
        visitor.approved_at = timezone.now()
        visitor.approved_by = request.user
        visitor.save()

        Notification.objects.create(
            user=request.user,
            sender=request.user,
            visitor=visitor,
            title="✅ Visitor Approved",
            message=f"{visitor.name} approved. Entry Code: {visitor.entry_code}"
        )

        messages.success(
            request,
            f"Visitor approved! Entry Code: {visitor.entry_code}"
        )

    except Visitor.DoesNotExist:
        messages.error(request, "Visitor not found")

    return redirect("resident_visitors")


@login_required
@role_required("resident")
def deny_visitor(request, id):
    try:
        visitor = Visitor.objects.get(
            id=id,
            apartment=request.user.userprofile.apartment,
            status="pending"
        )

        visitor.status = "rejected"
        visitor.rejected_at = timezone.now()
        visitor.save()

        Notification.objects.create(
            user=request.user,
            sender=request.user,
            visitor=visitor,
            title="❌ Visitor Rejected",
            message=f"{visitor.name} has been denied entry"
        )

        messages.warning(request, f"{visitor.name} has been denied")

    except Visitor.DoesNotExist:
        messages.error(request, "Visitor not found")

    return redirect("resident_visitors")


@login_required
@role_required("guard", "guard_admin")
def verify_entry_code(request, id):
    visitor = get_object_or_404(Visitor, id=id, status="approved")

    if request.method == "POST":
        code = request.POST.get("code")

        if code == visitor.entry_code:
            visitor.status = "checked_in"
            visitor.check_in_time = timezone.now()
            visitor.save()

            messages.success(request, "Visitor checked in successfully")
        else:
            messages.error(request, "Invalid entry code")

    return redirect("guard_dashboard")

@login_required
@role_required("resident")
def mark_exit(request, id):
    """
    Resident marks visitor exit (alternative to guard checkout)
    """
    try:
        visitor = Visitor.objects.get(
            id=id,
            apartment=request.user.userprofile.apartment
        )
        
        if visitor.status != "checked_in":
            messages.warning(request, "⚠️ Visitor is not checked in")
            return redirect("resident_visitors")

        # Calculate duration
        if visitor.check_in_time:
            duration = timezone.now() - visitor.check_in_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        else:
            duration_str = "Unknown"

        visitor.status = "checked_out"
        visitor.check_out_time = timezone.now()
        visitor.save()

        messages.success(
            request,
            f"✅ {visitor.name} marked as exited. Visit duration: {duration_str}"
        )

    except Visitor.DoesNotExist:
        messages.error(request, "❌ Visitor not found")

    return redirect("resident_visitors")






@role_required("resident")
def resident_services(request):
    """
    Browse available service providers for the logged-in resident
    """

    try:
        # ================= USER PROFILE =================
        user_profile = UserProfile.objects.select_related(
            "society", "apartment"
        ).get(user=request.user)

        society = user_profile.society

        user_city = society.city if society else ""
        user_area = (
            society.address.split(",")[0]
            if society and society.address
            else ""
        )

        # ================= SERVICES =================
        services = Service.objects.filter(active=True).order_by("name")

        # ================= FILTER PARAMS =================
        selected_service = request.GET.get("service", "").strip()
        search_query = request.GET.get("q", "").strip()
        search_area = request.GET.get("area", "").strip()

        # ================= PROVIDERS BASE QUERY =================
        providers = (
            ServiceProvider.objects.filter(
                verification_status="verified",
                is_available=True
            )
            .select_related("service")
        )

        # ================= FILTER: SERVICE =================
        if selected_service and selected_service.isdigit():
            providers = providers.filter(service_id=int(selected_service))

        # ================= FILTER: LOCATION =================
        if search_area:
            providers = providers.filter(
                Q(area__icontains=search_area) |
                Q(city__icontains=search_area)
            )
        elif user_city:
            providers = providers.filter(city__iexact=user_city)

        # ================= FILTER: SEARCH =================
        if search_query:
            providers = providers.filter(
                Q(name__icontains=search_query) |
                Q(service__name__icontains=search_query)
            )


        # ================= FINAL PROVIDERS =================
        service_providers = providers.order_by(
            "-rating",
            "-total_hires",
            "-experience_years"
        )[:50]

        # ================= HIRED SERVICES =================
        pending_hired_services = HiredService.objects.filter(
            resident=request.user,
            status="pending"
        ).select_related(
            "service_provider",
            "service_provider__service"
        )


        # 🔥 FIXED: removed extra bracket
        my_hired_services = HiredService.objects.filter(
            resident=request.user,
            status__in=["active", "paused"]
        ).select_related(
            "service_provider",
            "service_provider__service"
        )

        # ================= PROVIDER STATUS MAP =================
        provider_status_map = {}

        for hire in HiredService.objects.filter(resident=request.user):
            provider_status_map[hire.service_provider_id] = hire.status


        # ================= CONTEXT =================
        context = {
            "services": services,
            "service_providers": service_providers,

            # ✅ THESE MATCH YOUR TEMPLATE
            "pending_hired_services": pending_hired_services,
            "my_hired_services": my_hired_services,
            "provider_status_map": provider_status_map,
            "user_profile": user_profile,
            "user_city": user_city,
            "user_area": user_area,

            "selected_service": selected_service,
            "search_area": search_area,
            "search_query": search_query,
        }

        return render(request, "resident_services.html", context)

    except UserProfile.DoesNotExist:
        messages.error(
            request,
            "User profile not found. Please contact society admin."
        )
        return redirect("resident_dashboard")

    except Exception as e:
        raise e   # 👈 SHOW THE REAL ERROR



@login_required
@role_required("resident")
def hire_service_provider(request, provider_id):
    """
    Send hire request to a service provider (now creates pending request)
    """

    provider = get_object_or_404(
        ServiceProvider,
        id=provider_id,
        verification_status="verified",
        is_available=True
    )

    # ❌ Prevent duplicate hiring
    if HiredService.objects.filter(
        resident=request.user,
        service_provider=provider
    ).exists():
        messages.warning(
            request,
            f"You have already sent a request to {provider.name}"
        )
        return redirect("resident_services")

    # ✅ Create hire request with 'pending' status
    HiredService.objects.create(
        resident=request.user,
        service_provider=provider,
        start_date=now().date(),
        timing=provider.preferred_timings,
        days=provider.available_days,
        monthly_payment=provider.monthly_rate or 0,
        status="pending",  # ← CHANGED: Now starts as pending
    )

    # ✅ Update provider stats (total hires, but not active clients yet)
    provider.save()

    messages.success(
        request,
        f"✅ Hire request sent to {provider.name}. Waiting for acceptance."
    )

    return redirect("resident_services")


@login_required
@role_required("resident")
@require_POST
def toggle_hired_service(request, hired_id):
    """
    Toggle active/paused status of a hired service.
    ❌ Pending services cannot be toggled.
    """

    try:
        hired = HiredService.objects.get(
            id=hired_id,
            resident=request.user
        )

        # ❌ BLOCK pending requests
        if hired.status == "pending":
            return JsonResponse(
                {
                    "error": "This service request is still pending approval"
                },
                status=400
            )

        # ✅ TOGGLE only active <-> paused
        if hired.status == "active":
            hired.status = "paused"

        elif hired.status == "paused":
            hired.status = "active"

        else:
            return JsonResponse(
                {"error": "Invalid service status"},
                status=400
            )

        hired.save()

        return JsonResponse(
            {
                "success": True,
                "status": hired.status
            }
        )

    except HiredService.DoesNotExist:
        return JsonResponse(
            {"error": "Service not found"},
            status=404
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500
        )


@login_required
@role_required("resident")
def terminate_hired_service(request, hired_id):
    """
    Terminate a hired service
    """
    if request.method == 'POST':
        try:
            hired = HiredService.objects.get(id=hired_id, resident=request.user)
            
            # Update status
            hired.status = 'terminated'
            hired.end_date = request.POST.get('end_date') or now().date()
            hired.save()
            
            # Update provider stats
            provider = hired.service_provider
            provider.active_clients = max(0, provider.active_clients - 1)
            provider.save()
            
            messages.success(request, f"{hired.service_provider.name} has been removed from your services")
            
        except HiredService.DoesNotExist:
            messages.error(request, "Service not found")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('resident_services')


@login_required
@role_required("resident")
def service_provider_detail(request, provider_id):
    """
    View detailed information about a service provider
    """
    provider = get_object_or_404(
        ServiceProvider.objects.select_related('service'),
        id=provider_id
    )
    
    # Check if already hired
    hired_service = HiredService.objects.filter(
        resident=request.user,
        service_provider=provider,
        status='active'
    ).first()

    is_hired = hired_service is not None

    user_review = None
    if hired_service:
        user_review = ServiceReview.objects.filter(
            hired_service=hired_service
        ).first()

    
    # Get reviews
    reviews = ServiceReview.objects.filter(
        hired_service__service_provider=provider
    ).select_related('hired_service__resident')[:10]
    
    similar_providers = ServiceProvider.objects.filter(
        service=provider.service,
        city=provider.city,
        verification_status="verified",
        is_available=True
    ).exclude(
        id=provider.id
    ).order_by(
        "-rating", "-total_hires"
    )[:6]

    context = {
        'provider': provider,
        'is_hired': is_hired,
        'hired_service': hired_service,
        'user_review': user_review,
        'reviews': reviews,
        'similar_providers': similar_providers,
    }

    
    return render(request, 'service_provider_detail.html', context)





@login_required
@role_required("resident")
def resident_notices(request):
    """Display community feed, announcements, and polls"""
    try:
        profile = request.user.userprofile
        society = profile.society
        
        if not society:
            messages.error(request, "You are not associated with any society.")
            return redirect('home')
        
        # Fetch data filtered by society
        posts = CommunityPost.objects.filter(society=society).select_related('user', 'apartment')
        announcements = Announcement.objects.filter(society=society).select_related('created_by')
        polls = Poll.objects.filter(society=society).prefetch_related('options', 'poll_votes')
        
        # Check which polls the user has voted on
        user_voted_polls = PollVote.objects.filter(
            user=request.user,
            poll__society=society
        ).values_list('poll_id', flat=True)
        
        liked_post_ids = PostLike.objects.filter(
            user=request.user,
            post__society=society
        ).values_list('post_id', flat=True)

        context = {
            'posts': posts,
            'announcements': announcements,
            'polls': polls,
            'user_voted_polls': list(user_voted_polls),
            'user_apartment': profile.apartment,
            'liked_post_ids': list(liked_post_ids),
            'is_admin': profile.role in ['admin', 'society_admin'],
            'user_role': profile.role,
        }

        
        return render(request, "resident_notices.html", context)
    
    except Exception as e:
        messages.error(request, f"Error loading community page: {str(e)}")
        return redirect('home')


@login_required
@require_POST
def api_mark_all_chats_read(request):
    ChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    new_count = ChatMessage.objects.filter(
        receiver=request.user,
        is_read=False
    ).exclude(sender=request.user).count()

    return JsonResponse({
        'success': True,
        'total_unread': new_count
    })

@login_required
@role_required("resident")
def resident_notifications(request):
    user    = request.user
    profile = user.userprofile

    # ── Alerts / Notifications ─────────────────────────────────
    # Only notifications addressed to this user (visitor check-ins
    # for their flat are sent here by the guard check-in view)
    notifications = Notification.objects.filter(
        user=user
    ).order_by('-created_at')

    unread_qs = notifications.filter(is_read=False)
    unread_count = unread_qs.count()

    # Mark them read
    if unread_count > 0:
        unread_qs.update(is_read=True)

    # After updating → set unread_count = 0
    unread_count = 0

    # ── Bills assigned to this resident ────────────────────────
    # Auto-mark overdue rows before rendering
    today = timezone.now().date()
    BillPayer.objects.filter(
        user=user,
        status='pending',
        bill__due_date__lt=today
    ).update(status='overdue')

    all_bp = BillPayer.objects.filter(
        user=user
    ).select_related('bill').order_by('-bill__created_at')

    pending_bill_payers = [bp for bp in all_bp if bp.status == 'pending']
    overdue_bill_payers = [bp for bp in all_bp if bp.status == 'overdue']
    paid_bill_payers    = [bp for bp in all_bp if bp.status == 'paid']

    # ── Unread chat messages ────────────────────────────────────
    total_unread = ChatMessage.objects.filter(
        receiver=user,
        is_read=False
    ).exclude(sender=user).count()

    return render(request, 'resident_notifications.html', {
        'profile':              profile,
        'user':                 user,
        # Alerts
        'notifications':        notifications,
        'unread_count':         unread_count,
        # Payments
        'pending_bill_payers':  pending_bill_payers,
        'overdue_bill_payers':  overdue_bill_payers,
        'paid_bill_payers':     paid_bill_payers,
        'pending_bills_count':  len(pending_bill_payers),
        'overdue_bills_count':  len(overdue_bill_payers),
        'paid_bills_count':     len(paid_bill_payers),
        # Chat
        'total_unread':         total_unread,
    })


# ─────────────────────────────────────────
# POST /api/bills/pay/<bp_id>/
# Resident marks their own BillPayer row as paid
# ─────────────────────────────────────────
@login_required
@require_POST
def api_resident_pay_bill(request, bp_id):
    try:
        data      = json.loads(request.body)
        method    = data.get('method', 'upi')
        reference = data.get('reference', '').strip()

        bp = BillPayer.objects.select_related(
            'bill__society'
        ).get(id=bp_id, user=request.user)

        if bp.status == 'paid':
            return JsonResponse({'success': False, 'error': 'This bill is already paid'})

        bp.status            = 'paid'
        bp.paid_at           = timezone.now()
        bp.payment_reference = reference
        bp.save()

        # Update parent Bill status if everyone has paid
        bill = bp.bill
        if not bill.billpayer_set.filter(status__in=['pending', 'overdue']).exists():
            bill.status = 'paid'
            bill.save(update_fields=['status'])

        # Notify society admin
        try:
            admin_profile = bill.society.userprofile_set.filter(
                role='society_admin', status='approved'
            ).first()
            if admin_profile:
                Notification.objects.create(
                    user=admin_profile.user,
                    sender=request.user,
                    title=f"✅ Payment Received: {bill.title}",
                    message=(
                        f"{request.user.get_full_name() or request.user.username} "
                        f"paid ₹{bill.amount} via {method.upper()}."
                        + (f" Ref: {reference}" if reference else '')
                    )
                )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': f'Payment of ₹{bill.amount} recorded!'
        })

    except BillPayer.DoesNotExist:
        return JsonResponse(
            {'success': False, 'error': 'Bill not found or not assigned to you'}, status=404
        )
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})




@login_required
@role_required("resident", "society_admin")
def create_post(request):
    """Create a new community post"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            society = profile.society
            
            content = request.POST.get('content', '').strip()
            image = request.FILES.get('image')
            
            if not content:
                return JsonResponse({'success': False, 'error': 'Content is required'})
            
            post = CommunityPost.objects.create(
                society=society,
                user=request.user,
                apartment=profile.apartment,
                content=content,
                image=image
            )
            
            messages.success(request, 'Post created successfully!')
            return JsonResponse({'success': True, 'message': 'Post created successfully!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@role_required("resident", "society_admin")
def create_announcement(request):
    """Create a new announcement (only for admins/specific roles)"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            society = profile.society
            
            # Check if user has permission to create announcements
            if profile.role not in ['society_admin', 'admin']:
                return JsonResponse({
                    'success': False, 
                    'error': 'Only society admins can create announcements'
                })
            
            title = request.POST.get('title', '').strip()
            message = request.POST.get('message', '').strip()
            
            if not title or not message:
                return JsonResponse({
                    'success': False, 
                    'error': 'Title and message are required'
                })
            
            announcement = Announcement.objects.create(
                society=society,
                title=title,
                message=message,
                created_by=request.user
            )
            
            messages.success(request, 'Announcement created successfully!')
            return JsonResponse({'success': True, 'message': 'Announcement created successfully!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@role_required("resident", "society_admin")
def create_poll(request):
    """Create a new poll"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            society = profile.society
            
            question = request.POST.get('question', '').strip()
            options_json = request.POST.get('options', '[]')
            
            if not question:
                return JsonResponse({'success': False, 'error': 'Question is required'})
            
            try:
                options = json.loads(options_json)
            except:
                return JsonResponse({'success': False, 'error': 'Invalid options format'})
            
            if len(options) < 2:
                return JsonResponse({
                    'success': False, 
                    'error': 'At least 2 options are required'
                })
            
            # Create poll
            poll = Poll.objects.create(
                society=society,
                question=question,
                created_by=request.user
            )
            
            # Create poll options
            for option_text in options:
                if option_text.strip():
                    PollOption.objects.create(
                        poll=poll,
                        text=option_text.strip()
                    )
            
            messages.success(request, 'Poll created successfully!')
            return JsonResponse({'success': True, 'message': 'Poll created successfully!'})
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@role_required("resident", "society_admin")
def vote_poll(request, poll_id):
    """Vote on a poll option"""
    if request.method == 'POST':
        try:
            profile = request.user.userprofile
            society = profile.society
            
            poll = get_object_or_404(Poll, id=poll_id, society=society)
            option_id = request.POST.get('option_id')
            
            if not option_id:
                return JsonResponse({'success': False, 'error': 'Option is required'})
            
            option = get_object_or_404(PollOption, id=option_id, poll=poll)
            
            # Check if user already voted
            existing_vote = PollVote.objects.filter(poll=poll, user=request.user).first()
            
            if existing_vote:
                # Update vote
                old_option = existing_vote.option
                old_option.votes = F('votes') - 1
                old_option.save()
                
                existing_vote.option = option
                existing_vote.save()
                
                option.votes = F('votes') + 1
                option.save()
                
                message = 'Vote updated successfully!'
            else:
                # New vote
                PollVote.objects.create(
                    poll=poll,
                    option=option,
                    user=request.user
                )
                
                option.votes = F('votes') + 1
                option.save()
                
                message = 'Vote recorded successfully!'
            
            # Refresh to get updated counts
            option.refresh_from_db()
            
            return JsonResponse({
                'success': True, 
                'message': message,
                'votes': option.votes
            })
        
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@role_required("resident", "society_admin")
def like_post(request, post_id):
    if request.method != "POST":
        return JsonResponse({"success": False})

    post = get_object_or_404(CommunityPost, id=post_id)
    user = request.user

    like = PostLike.objects.filter(post=post, user=user).first()

    if like:
        like.delete()
        post.likes = F('likes') - 1
        liked = False
    else:
        PostLike.objects.create(post=post, user=user)
        post.likes = F('likes') + 1
        liked = True

    post.save()
    post.refresh_from_db()

    return JsonResponse({
        "success": True,
        "liked": liked,
        "likes": post.likes
    })

def post_detail(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    return render(request, "post_detail.html", {"post": post})

@login_required
def get_comments(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)

    comments = Comment.objects.filter(post=post).select_related('user')

    data = []
    for c in comments:
        data.append({
            "id": c.id,
            "user": c.user.get_full_name() or c.user.username,
            "text": c.text,
            "time": c.created_at.strftime("%d %b %Y, %I:%M %p"),
        })

    return JsonResponse({
        "success": True,
        "comments": data,
        "count": comments.count()
    })

@login_required
@role_required("resident", "society_admin")
def add_comment(request, post_id):
    if request.method != "POST":
        return JsonResponse({"success": False})

    post = get_object_or_404(CommunityPost, id=post_id)
    text = request.POST.get("text", "").strip()

    if not text:
        return JsonResponse({"success": False, "error": "Comment cannot be empty"})

    Comment.objects.create(
        post=post,
        user=request.user,
        text=text
    )

    # 🔥 Update counter on post
    post.comments = Comment.objects.filter(post=post).count()
    post.save(update_fields=["comments"])

    return JsonResponse({
        "success": True,
        "new_count": post.comments
    })

@login_required
@role_required("guard", "guard_admin")

def guard_dashboard(request):
    """
    Guard Dashboard
    Real-life guard workflow using existing models only
    """

    # ================= TIMEZONE =================
    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    today = now.date()

    # ================= USER / SOCIETY =================
    profile = request.user.userprofile
    society = profile.society

    # ================= GREETING =================
    hour = now.hour
    if hour < 12:
        greeting = "morning"
    elif hour < 17:
        greeting = "afternoon"
    else:
        greeting = "evening"

    # ================= TODAY ENTRIES =================
    today_entries = Visitor.objects.filter(
        society=society,
        check_in_time__date=today,
        status__in=["checked_in", "checked_out"],
    ).count()

    # ================= PENDING VISITORS =================
    pending_visitors = Visitor.objects.filter(
        society=society,
        status="pending"
    ).select_related("apartment").order_by("-created_at")[:10]

    pending_count = pending_visitors.count()

    # ================= RECENT CHECK-INS =================
    recent_checkins = Visitor.objects.filter(
        society=society,
        status="checked_in",
        check_in_time__date=today
    ).select_related("apartment").order_by("-check_in_time")[:10]

    # ================= PARCELS TODAY =================
    parcels_today = Delivery.objects.filter(
        apartment__society=society,
        received_at__date=today
    ).count()

    # ================= GUARD SHIFT =================
    current_shift = GuardShift.objects.filter(
        guard=profile,
        date=today
    ).first()

    # ================= TODAY TASKS =================

    # Patrol
    active_patrol = PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="active"
    ).first()

    completed_patrol = PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="completed",
        start_time__date=today
    ).exists()

    patrol_completed = bool(completed_patrol)

    # Shift handover logic
    shift_handover_done = bool(
        current_shift and current_shift.check_out
    )

    tasks = {
        "patrol_active": bool(active_patrol),
        "patrol_completed": patrol_completed,
        "handover_done": shift_handover_done,
    }

    # ================= LEADERBOARD (WEEKLY – REAL DATA) =================
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    leaderboard = []

    guards = UserProfile.objects.filter(
        society=society,
        role__in=["guard", "guard_admin"],
        status="approved"
    )


    for guard in guards:
        user = guard.user

        visitor_checkins = Visitor.objects.filter(
            checked_in_by=user,
            check_in_time__date__range=(week_start, week_end)
        ).count()

        visitor_checkouts = Visitor.objects.filter(
            checked_out_by=user,
            check_out_time__date__range=(week_start, week_end)
        ).count()

        help_attendance = DailyHelpAttendance.objects.filter(
            check_in__date__range=(week_start, week_end)
        ).count()

        patrols_completed = PatrolRound.objects.filter(
            guard=guard,
            status="completed",
            start_time__date__range=(week_start, week_end)
        ).count()

        points = (
            visitor_checkins * 10 +
            visitor_checkouts * 5 +
            help_attendance * 5 +
            patrols_completed * 20
        )

        if points > 0:
            leaderboard.append({
                "user": user,
                "points": points,
                "entries": visitor_checkins,
            })

    leaderboard = sorted(
        leaderboard,
        key=lambda x: x["points"],
        reverse=True
    )[:10]

    # ================= NOTIFICATIONS =================
    guard_notification_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # ================= CONTEXT =================
    context = {
        # Time
        "greeting": greeting,
        "current_time": now.strftime("%I:%M %p"),
        "today_date": today.strftime("%d %B %Y"),

        # Stats
        "today_entries": today_entries,
        "pending_count": pending_count,
        "parcels_today": parcels_today,

        # Lists
        "pending_visitors": pending_visitors,
        "recent_checkins": recent_checkins,
        "leaderboard": leaderboard,

        # Tasks
        "tasks": tasks,

        # Shift
        "current_shift": current_shift,

        # Notifications
        "guard_notification_count": guard_notification_count,

        # User
        "guard_name": request.user.first_name or request.user.username,
        "society_name": society.name if society else "MyGate Society",
        "available_months": _available_months(),
        "today_month":      timezone.now().astimezone(
                                pytz.timezone("Asia/Kolkata")
                            ).strftime("%Y-%m"),
    }

    return render(request, "society_guard/guard_index.html", context)

def _available_months(n=6):
    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    months = []
    year, month = now.year, now.month
    for i in range(n):
        val = f"{year}-{month:02d}"
        months.append({
            "value": val,
            "label": date(year, month, 1).strftime("%B %Y"),
            "selected": i == 0,
        })
        # go back one month
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months
# ──────────────────────────────────────────────────────────────
#  HELPER: parse "YYYY-MM" from request, default to current month
# ──────────────────────────────────────────────────────────────
def _parse_month(request):
    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    raw = request.GET.get("month", "")
    try:
        year, month = map(int, raw.split("-"))
        return year, month
    except Exception:
        return now.year, now.month


# ──────────────────────────────────────────────────────────────
#  HELPER: build attendance records for a guard for a month
# ──────────────────────────────────────────────────────────────
def _get_attendance_data(guard_profile, year, month):
    """
    Returns (records_list, summary_dict) for the given guard & month.
    Each record is a dict with: date, date_display, status,
    check_in, check_out, duration_minutes, duration_display.
    """
    india_tz = pytz.timezone("Asia/Kolkata")
    today = timezone.now().astimezone(india_tz).date()

    # Days in month
    _, days_in_month = calendar.monthrange(year, month)
    start_date = date(year, month, 1)
    end_date   = date(year, month, days_in_month)

    # Fetch all shifts for this guard in this month
    shifts = GuardShift.objects.filter(
        guard=guard_profile,
        date__range=(start_date, end_date)
    ).order_by("date")

    shift_map = {s.date: s for s in shifts}

    records = []
    summary = {"present": 0, "absent": 0, "late": 0, "total_minutes": 0, "worked_days": 0}

    for day_offset in range(days_in_month):
        d = start_date + timedelta(days=day_offset)
        if d > today:
            # Future – skip
            continue

        shift = shift_map.get(d)

        if shift is None:
            # No shift assigned → absent (unless it's a known holiday/leave)
            record = {
                "date": d.isoformat(),
                "date_display": d.strftime("%d %b, %a"),
                "status": "absent",
                "check_in": None,
                "check_out": None,
                "duration_minutes": None,
                "duration_display": "—",
            }
            summary["absent"] += 1
        else:
            check_in_time  = None
            check_out_time = None
            duration_min   = None
            duration_disp  = "—"
            status         = "absent"

            if shift.check_in:
                ci_local = shift.check_in.astimezone(india_tz)
                check_in_time = ci_local.strftime("%I:%M %p")

                # Late check-in: more than 15 min after shift start
                shift_start = india_tz.localize(
                    timezone.datetime.combine(d, shift.start_time)
                )
                late_by = (ci_local - shift_start).total_seconds() / 60
                status = "late" if late_by > 15 else "present"

                if shift.check_out:
                    co_local = shift.check_out.astimezone(india_tz)
                    check_out_time = co_local.strftime("%I:%M %p")
                    duration_min   = int((co_local - ci_local).total_seconds() / 60)
                    hours   = duration_min // 60
                    minutes = duration_min % 60
                    duration_disp = f"{hours}h {minutes}m"
                    summary["total_minutes"] += duration_min
                    summary["worked_days"]   += 1

                if status == "late":
                    summary["late"]    += 1
                    summary["present"] += 1          # late counts as present too
                else:
                    summary["present"] += 1
            else:
                summary["absent"] += 1

            record = {
                "date": d.isoformat(),
                "date_display": d.strftime("%d %b, %a"),
                "status": status,
                "check_in": check_in_time,
                "check_out": check_out_time,
                "duration_minutes": duration_min,
                "duration_display": duration_disp,
            }

        records.append(record)

    # Average hours
    if summary["worked_days"] > 0:
        avg_min = summary["total_minutes"] / summary["worked_days"]
        summary["avg_hours"] = f"{int(avg_min//60)}h {int(avg_min%60)}m"
    else:
        summary["avg_hours"] = "—"

    return list(reversed(records)), summary   # most-recent first for display


# ──────────────────────────────────────────────────────────────
#  VIEW 1: JSON for the table (AJAX)
# ──────────────────────────────────────────────────────────────
@login_required(login_url="login")
def guard_attendance_json(request):
    profile = request.user.userprofile
    year, month = _parse_month(request)
    records, summary = _get_attendance_data(profile, year, month)
    return JsonResponse({"records": records, "summary": summary})


# ──────────────────────────────────────────────────────────────
#  VIEW 2: XLS download
# ──────────────────────────────────────────────────────────────
@login_required(login_url="login")
def guard_attendance_download(request):
    profile = request.user.userprofile
    year, month = _parse_month(request)
    records_desc, summary = _get_attendance_data(profile, year, month)
    records = list(reversed(records_desc))   # chronological for XLS

    # ── Build workbook ──
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Attendance"

    # ── Color palette ──
    C_HEADER_BG  = "1A237E"   # dark navy
    C_HEADER_FG  = "FFFFFF"
    C_SUBHEADER  = "E8EAF6"   # light indigo tint
    C_PRESENT    = "D1FAE5"
    C_ABSENT     = "FEE2E2"
    C_LATE       = "FEF3C7"
    C_ALT_ROW    = "F8FAFC"
    C_SUMMARY_BG = "EEF2FF"

    thin = Side(style="thin", color="DEE2E6")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    # ── Column widths ──
    col_widths = [5, 18, 16, 14, 14, 16]
    for i, w in enumerate(col_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    # ── Title block ──
    ws.merge_cells("A1:F1")
    title_cell = ws["A1"]
    title_cell.value = "MyGate — Guard Attendance Report"
    title_cell.font = Font(name="Arial", bold=True, size=14, color=C_HEADER_FG)
    title_cell.fill = PatternFill("solid", fgColor=C_HEADER_BG)
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 32

    ws.merge_cells("A2:F2")
    month_label = date(year, month, 1).strftime("%B %Y")
    guard_name  = request.user.get_full_name() or request.user.username
    sub_cell = ws["A2"]
    sub_cell.value = f"{guard_name}  ·  {month_label}  ·  Society: {profile.society.name if profile.society else '—'}"
    sub_cell.font = Font(name="Arial", size=10, color="475569")
    sub_cell.fill = PatternFill("solid", fgColor=C_SUBHEADER)
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 20

    # blank spacer
    ws.row_dimensions[3].height = 6

    # ── Summary row ──
    ws["A4"] = "Present"
    ws["B4"] = summary["present"]
    ws["C4"] = "Absent"
    ws["D4"] = summary["absent"]
    ws["E4"] = "Late Days"
    ws["F4"] = summary["late"]

    ws["A5"] = "Avg Hours/Day"
    ws["B5"] = summary["avg_hours"]

    for row in [4, 5]:
        for col in range(1, 7):
            cell = ws.cell(row=row, column=col)
            cell.fill = PatternFill("solid", fgColor=C_SUMMARY_BG)
            cell.font = Font(name="Arial", size=10, bold=(col % 2 == 1))
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
        ws.row_dimensions[row].height = 18

    ws.row_dimensions[6].height = 8   # spacer

    # ── Table header ──
    headers = ["#", "Date", "Status", "Check-In", "Check-Out", "Duration"]
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col)
        cell.value = h
        cell.font = Font(name="Arial", bold=True, size=10, color=C_HEADER_FG)
        cell.fill = PatternFill("solid", fgColor=C_HEADER_BG)
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border
    ws.row_dimensions[7].height = 22

    # ── Data rows ──
    status_bg = {
        "present": C_PRESENT,
        "late":    C_LATE,
        "absent":  C_ABSENT,
        "holiday": "EDE9FE",
        "leave":   "E0F2FE",
    }
    status_label = {
        "present": "✓ Present",
        "late":    "⏰ Late",
        "absent":  "✗ Absent",
        "holiday": "🎉 Holiday",
        "leave":   "🏖 Leave",
    }

    for i, r in enumerate(records, 1):
        row_num  = 7 + i
        row_bg   = C_ALT_ROW if i % 2 == 0 else "FFFFFF"
        status   = r["status"]
        stat_bg  = status_bg.get(status, "FFFFFF")

        data = [
            i,
            r["date_display"],
            status_label.get(status, status.title()),
            r["check_in"]  or "—",
            r["check_out"] or "—",
            r["duration_display"],
        ]

        for col, val in enumerate(data, 1):
            cell = ws.cell(row=row_num, column=col)
            cell.value = val
            cell.font  = Font(name="Arial", size=10)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border
            # status column gets coloured background
            if col == 3:
                cell.fill = PatternFill("solid", fgColor=stat_bg)
                cell.font = Font(name="Arial", size=10, bold=True)
            else:
                cell.fill = PatternFill("solid", fgColor=row_bg)

        ws.row_dimensions[row_num].height = 18

    # ── Footer ──
    footer_row = 7 + len(records) + 2
    ws.merge_cells(f"A{footer_row}:F{footer_row}")
    fc = ws[f"A{footer_row}"]
    from django.utils import timezone as dj_tz
    fc.value = f"Generated on {dj_tz.now().strftime('%d %b %Y %I:%M %p')} IST · MyGate Society Management"
    fc.font = Font(name="Arial", size=9, italic=True, color="94A3B8")
    fc.alignment = Alignment(horizontal="center")

    # ── Freeze panes ──
    ws.freeze_panes = "A8"

    # ── Stream response ──
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"attendance_{guard_name.replace(' ','_')}_{year}_{month:02d}.xlsx"
    response = HttpResponse(
        buffer,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response

@login_required
@role_required("guard", "guard_admin")

def complete_handover(request):
    """
    Mark guard shift handover (auto-create shift if missing)
    """
    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    today = now.date()

    profile = request.user.userprofile
    society = profile.society

    # 🔹 Get or create today's shift
    shift, created = GuardShift.objects.get_or_create(
        guard=profile,
        society=society,
        date=today,
        defaults={
            "shift_type": "morning",
            "check_in": now,
            "status": "active",
        }
    )


    # 🔹 If already handed over
    if shift.check_out:
        messages.warning(
            request,
            "⚠️ Shift handover already completed."
        )
        return redirect("guard_dashboard")

    # 🔹 Complete handover
    shift.check_out = now
    shift.status = "completed"
    shift.is_present = False
    shift.save()

    messages.success(
        request,
        f"✅ Shift handover completed at {now.strftime('%I:%M %p')}"
    )

    return redirect("guard_dashboard")


from django.db.models import Count, Q, Avg
from datetime import datetime, time

def mark_check_in(shift: GuardShift):
    """
    Called when guard checks in
    """
    shift.check_in = timezone.now()
    shift.status = 'active'
    shift.save(update_fields=['check_in', 'status'])


def mark_check_out(shift: GuardShift):
    """
    Called when guard checks out
    """
    shift.check_out = timezone.now()
    shift.status = 'completed'
    shift.save(update_fields=['check_out', 'status'])


@login_required
@role_required("guard_admin")
@require_POST
def override_attendance(request):
    """
    Guard admin manually marks attendance
    """
    shift_id = request.POST.get("shift_id")
    status = request.POST.get("status")

    shift = get_object_or_404(
        GuardShift,
        id=shift_id,
        society=request.user.userprofile.society,
        guard__role="guard"  # Only allow for regular guards
    )

    if status not in dict(GuardShift.ATTENDANCE_OVERRIDE):
        return JsonResponse({"success": False, "error": "Invalid status"})

    shift.attendance_override = status
    shift.attendance_marked_by = request.user
    shift.attendance_marked_at = timezone.now()
    shift.save(update_fields=[
        "attendance_override",
        "attendance_marked_by",
        "attendance_marked_at"
    ])

    return JsonResponse({"success": True})


@login_required
def guard_apply_leave(request):
    """Guard applies for leave"""
    if request.method == 'POST':
        profile = request.user.userprofile
        society = profile.society
        
        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '').strip()
        
        if not all([leave_type, start_date, end_date, reason]):
            return JsonResponse({
                'success': False,
                'error': 'All fields are required'
            })
        
        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Validation
        if start_date < timezone.now().date():
            return JsonResponse({
                'success': False,
                'error': 'Start date cannot be in the past'
            })
        
        if end_date < start_date:
            return JsonResponse({
                'success': False,
                'error': 'End date must be after start date'
            })
        
        # Create leave request
        leave = LeaveRequest.objects.create(
            guard=profile,
            society=society,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )
        
        # Create notification for guard admin
        guard_admins = UserProfile.objects.filter(
            society=society,
            role='guard_admin',
            status='approved'
        )
        
        for admin_profile in guard_admins:
            Notification.objects.create(
                user=admin_profile.user,
                sender=request.user,
                title='📅 New Leave Request',
                message=f"{request.user.get_full_name() or request.user.username} has requested {leave.total_days} day(s) of {leave.get_leave_type_display()} leave from {start_date} to {end_date}."
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Leave request submitted successfully for {leave.total_days} day(s)'
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@role_required("guard_admin")
def guard_admin_leaves_page(request):
    profile = request.user.userprofile
    society = profile.society
    
    pending_leaves = LeaveRequest.objects.filter(
        society=society,
        status='pending'
    ).select_related('guard__user')
    
    approved_leaves = LeaveRequest.objects.filter(
        society=society,
        status='approved'
    ).select_related('guard__user')
    
    rejected_leaves = LeaveRequest.objects.filter(
        society=society,
        status='rejected'
    ).select_related('guard__user')
    
    return render(request, 'society_guard/guard_admin_leaves.html', {
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'pending_count': pending_leaves.count(),
    })
# Guard-Admin Chat
@login_required
def guard_send_message(request):
    """Guard sends message to admin"""
    if request.method == 'POST':
        profile = request.user.userprofile
        society = profile.society
        
        message = request.POST.get('message', '').strip()
        message_type = request.POST.get('message_type', 'general')
        
        if not message:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            })
        
        # Create chat message
        chat = GuardAdminChat.objects.create(
            society=society,
            guard=profile,
            sender=request.user,
            message=message,
            message_type=message_type
        )
        
        # Notify guard admins
        guard_admins = UserProfile.objects.filter(
            society=society,
            role='guard_admin',
            status='approved'
        )
        
        for admin_profile in guard_admins:
            Notification.objects.create(
                user=admin_profile.user,
                sender=request.user,
                title='💬 New Message from Guard',
                message=f"{request.user.get_full_name() or request.user.username}: {message[:50]}..."
            )
        
        return JsonResponse({
            'success': True,
            'message_id': chat.id,
            'timestamp': chat.created_at.strftime('%I:%M %p')
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Guard Admin - Manage Leaves
@login_required
def guard_admin_manage_leaves(request):
    """Guard admin views and manages leave requests"""
    profile = request.user.userprofile
    society = profile.society
    
    # Get all leave requests
    pending_leaves = LeaveRequest.objects.filter(
        society=society,
        status='pending'
    ).select_related('guard__user')
    
    approved_leaves = LeaveRequest.objects.filter(
        society=society,
        status='approved'
    ).select_related('guard__user')
    
    rejected_leaves = LeaveRequest.objects.filter(
        society=society,
        status='rejected'
    ).select_related('guard__user')
    
    context = {
        'pending_leaves': pending_leaves,
        'approved_leaves': approved_leaves,
        'rejected_leaves': rejected_leaves,
        'pending_count': pending_leaves.count(),
    }
    
    return context



@login_required
@require_POST
def guard_admin_approve_leave(request, leave_id):
    try:
        profile = request.user.userprofile

        # Guard: only guard_admin can approve
        if profile.role != "guard_admin":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

        society = profile.society

        leave = get_object_or_404(LeaveRequest, id=leave_id, society=society)

        if leave.status != "pending":
            return JsonResponse({"success": False, "error": "Leave is no longer pending"}, status=400)

        # Parse optional remark
        try:
            data = json.loads(request.body)
            remarks = data.get("remarks", "").strip()
        except (json.JSONDecodeError, Exception):
            remarks = ""

        leave.status        = "approved"
        leave.reviewed_by   = request.user   # User, not UserProfile
        leave.reviewed_at   = timezone.now()
        leave.admin_remarks = remarks
        leave.save()

        # Create notification for the guard (safe — handles missing fields gracefully)
        _create_leave_notification(
            target_user=leave.guard.user,
            title="Leave Approved ✅",
            message=(
                f"Your {leave.get_leave_type_display()} leave "
                f"({leave.start_date} – {leave.end_date}) has been approved."
                + (f" Remark: {remarks}" if remarks else "")
            ),
        )

        return JsonResponse({"success": True, "message": "Leave approved successfully."})

    except Exception as e:
        traceback.print_exc()   # prints full error to your Django console
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@login_required
def guard_chat_list(request):
    """
    WhatsApp-style chat list for guards.
    The actual chat data is loaded via /api/chats/ AJAX.
    """
    return render(request, 'society_guard/guard_chat_list.html')


@login_required
def guard_chat_room(request, chat_id):
    """
    WhatsApp-style chat room for guards.
    Messages are loaded via /api/chats/<chat_id>/messages/ AJAX.
    """
    # Verify this chat belongs to the current user
    from .models import ChatRoom
    chat = get_object_or_404(
        ChatRoom,
        id=chat_id
    )
    # Security: make sure user is part of this chat
    if chat.user1 != request.user and chat.user2 != request.user:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("You are not part of this chat.")

    return render(request, 'society_guard/guard_chat_room.html', {
        'chat_id': chat_id,
    })

@login_required
@require_POST
def guard_admin_reject_leave(request, leave_id):
    try:
        profile = request.user.userprofile

        if profile.role != "guard_admin":
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

        society = profile.society

        leave = get_object_or_404(LeaveRequest, id=leave_id, society=society)

        if leave.status != "pending":
            return JsonResponse({"success": False, "error": "Leave is no longer pending"}, status=400)

        try:
            data = json.loads(request.body)
            remarks = data.get("remarks", "").strip()
        except (json.JSONDecodeError, Exception):
            remarks = ""

        leave.status        = "rejected"
        leave.reviewed_by   = request.user 
        leave.reviewed_at   = timezone.now()
        leave.admin_remarks = remarks
        leave.save()

        _create_leave_notification(
            target_user=leave.guard.user,
            title="Leave Rejected ❌",
            message=(
                f"Your {leave.get_leave_type_display()} leave "
                f"({leave.start_date} – {leave.end_date}) has been rejected."
                + (f" Reason: {remarks}" if remarks else "")
            ),
        )

        return JsonResponse({"success": True, "message": "Leave rejected."})

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)

def _create_leave_notification(target_user, title, message):
    """
    Safely create a Notification — handles models that may or may not have
    a notification_type field.
    """
    try:
        # Try with notification_type first (if your model has it)
        Notification.objects.create(
            user=target_user,
            title=title,
            message=message,
            notification_type="leave_update",
        )
    except TypeError:
        # Model doesn't have notification_type — create without it
        try:
            Notification.objects.create(
                user=target_user,
                title=title,
                message=message,
            )
        except Exception:
            # Notification creation is non-critical — don't let it crash the response
            traceback.print_exc()
    except Exception:
        traceback.print_exc()





# Manual Shift Creation with Custom Timings
@login_required
@require_POST
def guard_admin_create_custom_shift(request):
    """Create shift with custom timings"""
    profile = request.user.userprofile
    society = profile.society
    
    shift_name = request.POST.get('shift_name')
    date = request.POST.get('date')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time')
    guards = request.POST.getlist('guards')
    
    if not all([shift_name, date, start_time, end_time, guards]):
        return JsonResponse({
            'success': False,
            'error': 'All fields are required'
        })
    
    # Convert date and times
    shift_date = datetime.strptime(date, '%Y-%m-%d').date()
    start_time_obj = datetime.strptime(start_time, '%H:%M').time()
    end_time_obj = datetime.strptime(end_time, '%H:%M').time()
    
    created_count = 0
    for guard_id in guards:
        guard_profile = UserProfile.objects.filter(
            id=guard_id,
            society=society,
            role='guard',
            status='approved'
        ).first()
        
        if not guard_profile:
            continue
        
        # Check for leave
        on_leave = LeaveRequest.objects.filter(
            guard=guard_profile,
            status='approved',
            start_date__lte=shift_date,
            end_date__gte=shift_date
        ).exists()
        
        if on_leave:
            continue  # Skip guards on leave
        
        shift, created = GuardShift.objects.get_or_create(
            society=society,
            guard=guard_profile,
            date=shift_date,
            defaults={
                'shift_type': 'custom',
                'shift_name': shift_name,
                'start_time': start_time_obj,
                'end_time': end_time_obj,
            }
        )
        
        if created:
            created_count += 1
    
    return JsonResponse({
        'success': True,
        'message': f'Created {created_count} custom shift(s) for {shift_name}'
    })


print("✅ Attendance and Leave Management System Code Generated")
print("Add these models and views to your Django project")



@login_required
@role_required("guard", "guard_admin")
def guard_get_messages(request):
    """Get chat messages between guard and admin"""
    try:
        profile = request.user.userprofile
        society = profile.society
        
        # Get all messages for this guard
        messages_qs = GuardAdminChat.objects.filter(
            society=society,
            guard=profile
        ).select_related('sender').order_by('created_at')
        
        messages_data = []
        for msg in messages_qs:
            messages_data.append({
                'id': msg.id,
                'message': msg.message,
                'sender': msg.sender.username,
                'sender_name': msg.sender.get_full_name() or msg.sender.username,
                'time': msg.created_at.strftime('%I:%M %p'),
                'is_read': msg.is_read
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'messages': []
        })

@login_required
@role_required("guard_admin")
def guard_admin_management(request):
    """
    Main Guard Management Dashboard
    Shows ALL guards (excluding guard_admin) in attendance, even without shifts
    Stats calculation also excludes guard_admin
    """
    profile = request.user.userprofile
    society = profile.society
    today = timezone.localdate()

    # ================= GET ALL GUARDS (EXCLUDE GUARD_ADMIN) =================
    guards = UserProfile.objects.filter(
        society=society,
        role="guard",  # Only regular guards, not guard_admin
        status="approved"
    ).select_related("user").order_by("user__username")

    total_guards = guards.count()

    # ================= SHIFTS (EXCLUDE GUARD_ADMIN) =================
    today_shifts = GuardShift.objects.filter(
        society=society,
        date=today,
        guard__role="guard"  # Only regular guard shifts
    ).select_related("guard__user")

    active_shifts = today_shifts.filter(
        check_in__isnull=False,
        check_out__isnull=True
    ).count()

    # ================= BUILD ALL GUARDS ATTENDANCE LIST =================
    shifts_by_guard = {
        shift.guard_id: shift
        for shift in today_shifts
    }

    all_guards_attendance = []

    india_tz = pytz.timezone("Asia/Kolkata")

    for guard in guards:
        shift = shifts_by_guard.get(guard.id)

        # ✅ ADD LATE CALCULATION HERE
        if shift:
            is_late_checkin = False

            if shift.check_in and shift.start_time:
                shift_start_datetime = timezone.make_aware(
                    datetime.combine(shift.date, shift.start_time),
                    timezone=india_tz
                )

                check_in_aware = shift.check_in.astimezone(india_tz)

                time_diff_minutes = (
                    check_in_aware - shift_start_datetime
                ).total_seconds() / 60

                is_late_checkin = time_diff_minutes > 15

            # attach to object
            shift.is_late = is_late_checkin

        all_guards_attendance.append({
            'guard': guard,
            'shift': shift
        })


    # ================= ATTENDANCE RECORDS FOR SHIFTS TAB =================
    attendance_records = today_shifts.order_by(
        "shift_type",
        "guard__user__username"
    )

    # ================= PATROLS (EXCLUDE GUARD_ADMIN) =================
    active_patrol_details = PatrolRound.objects.filter(
        society=society,
        status="active",
        guard__role="guard"  # Only regular guards
    ).select_related("guard__user")

    active_patrol_count = active_patrol_details.count()

    completed_patrols_today = PatrolRound.objects.filter(
        society=society,
        status="completed",
        start_time__date=today,
        guard__role="guard"  # Only regular guards
    ).count()

    # Calculate total checkpoints scanned today (only for regular guards)
    total_checkpoints_today = CheckpointScan.objects.filter(
        patrol_round__society=society,
        patrol_round__guard__role="guard",  # Only regular guards
        scanned_at__date=today
    ).count()

    # Calculate incidents today (only reported by regular guards)
    incidents_today = IncidentReport.objects.filter(
        society=society,
        reported_at__date=today,
        reported_by__userprofile__role="guard"  # Only regular guards
    ).count()

    # ================= MONTHLY STATS (EXCLUDE GUARD_ADMIN) =================
    month_start = today.replace(day=1)
    
    # Only get shifts for regular guards, not guard_admin
    monthly_shifts = GuardShift.objects.filter(
        society=society,
        date__gte=month_start,
        date__lte=today,
        guard__role="guard"  # ✅ CRITICAL: Only regular guards
    )
    
    total_monthly_shifts = monthly_shifts.count()
    
    # Calculate completed shifts (either checked out OR manually marked present)
    completed_monthly_shifts = monthly_shifts.filter(
        Q(check_out__isnull=False) | Q(attendance_override='present')
    ).count()
    
    # Calculate absent shifts (no check-in AND not manually marked as present/late)
    absent_shifts = monthly_shifts.filter(
        Q(check_in__isnull=True) & 
        Q(attendance_override__in=['auto', 'absent'])
    ).count()
    
    # Calculate late check-ins (checked in more than 15 mins after shift start)
    late_checkins = 0
    for shift in monthly_shifts.filter(Q(check_in__isnull=False) | Q(attendance_override='late')):
        # If manually marked as late
        if shift.attendance_override == 'late':
            late_checkins += 1
            continue
            
        # If auto-calculated as late
        if shift.start_time and shift.check_in:
            shift_datetime = timezone.make_aware(
                datetime.combine(shift.date, shift.start_time)
            )
            
            time_diff = (shift.check_in - shift_datetime).total_seconds() / 60
            if time_diff > 15:  # More than 15 minutes late
                late_checkins += 1
    
    # Calculate attendance rate
    if total_monthly_shifts > 0:
        attendance_rate = int((completed_monthly_shifts / total_monthly_shifts) * 100)
    else:
        attendance_rate = 0
    
    # Leave days (manually marked as leave)
    leave_days = monthly_shifts.filter(attendance_override='leave').count()

    # ================= CONTEXT =================
    context = {
        # Header
        "society_name": society.name,
        "current_date": today.strftime("%d %B %Y"),
        "today_date": today.isoformat(),

        # Stats (all exclude guard_admin)
        "total_guards": total_guards,
        "active_shifts": active_shifts,
        "on_patrol": active_patrol_count,
        "today_shifts_count": today_shifts.count(),

        # ALL Guards with their shifts (or None)
        "all_guards_attendance": all_guards_attendance,
        
        # For shift schedule display
        "attendance_records": attendance_records,
        
        # For modal - all guards list (excluding guard_admin)
        "guards": guards,

        # Patrol (only regular guards)
        "active_patrols": active_patrol_details,
        "active_patrol_count": active_patrol_count,
        "completed_patrols_today": completed_patrols_today,
        "total_checkpoints_today": total_checkpoints_today,
        "incidents_today": incidents_today,
        
        # Monthly Stats (only regular guards)
        "attendance_rate": attendance_rate,
        "late_checkins": late_checkins,
        "absences": absent_shifts,
        "leave_days": leave_days,
    }

    return render(
        request,
        "society_guard/guard_admin_management.html",
        context
    )




@login_required
@role_required("guard_admin")
def create_shift(request):
    """
    Create new shift assignments (for guards only, not guard_admin)
    """
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    date_str = request.POST.get("date")
    shift_type = request.POST.get("shift_type")
    guards = request.POST.getlist("guards")

    if not date_str or not shift_type or not guards:
        messages.error(
            request,
            "⚠️ Please select date, shift type, and at least one guard."
        )
        return redirect("guard_admin_management")

    try:
        shift_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "⚠️ Invalid date format")
        return redirect("guard_admin_management")

    society = request.user.userprofile.society
    
    # Define shift times based on shift type
    shift_times = {
        "morning": ("06:00:00", "14:00:00"),
        "afternoon": ("14:00:00", "22:00:00"),
        "night": ("22:00:00", "06:00:00"),
    }
    
    start_time_str, end_time_str = shift_times.get(shift_type, ("06:00:00", "14:00:00"))
    start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
    end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

    created_count = 0
    for guard_id in guards:
        # Verify this is a regular guard, not guard_admin
        guard_profile = UserProfile.objects.filter(
            id=guard_id,
            society=society,
            role="guard",
            status="approved"
        ).first()
        
        if not guard_profile:
            continue
            
        shift, created = GuardShift.objects.get_or_create(
            society=society,
            guard=guard_profile,
            date=shift_date,
            shift_type=shift_type,
            defaults={
                "start_time": start_time,
                "end_time": end_time,
            }
        )
        if created:
            created_count += 1

    if created_count > 0:
        messages.success(
            request, 
            f"✓ Successfully created {created_count} shift(s) for {shift_date.strftime('%d %B %Y')}"
        )
    else:
        messages.warning(
            request,
            "⚠️ All selected guards already have shifts for this date and type"
        )
    
    return redirect("guard_admin_management")




@login_required
@role_required("guard_admin")
def shift_detail(request, shift_id):
    """
    View detailed information about a specific shift
    """
    shift = get_object_or_404(
        GuardShift,
        id=shift_id,
        society=request.user.userprofile.society
    )
    
    # Get patrol rounds for this shift
    patrol_rounds = PatrolRound.objects.filter(
        guard=shift.guard,
        start_time__date=shift.date
    ).prefetch_related('scans__checkpoint')
    
    # Get incidents reported during this shift using IncidentReport
    incidents = IncidentReport.objects.filter(
        reported_by=shift.guard.user,
        reported_at__date=shift.date
    )
    
    context = {
        "shift": shift,
        "patrol_rounds": patrol_rounds,
        "incidents": incidents,
    }

    return render(
        request,
        "society_guard/shift_detail.html",
        context
    )


@login_required
@role_required("guard_admin")
def filter_attendance(request):
    """
    Filter attendance by date - Shows ALL guards with late detection
    """
    date_str = request.GET.get("date")
    society = request.user.userprofile.society
    india_tz = pytz.timezone("Asia/Kolkata")
    
    if not date_str:
        return JsonResponse({"error": "Date required"}, status=400)
    
    try:
        filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"error": "Invalid date format"}, status=400)
    
    guards = UserProfile.objects.filter(
        society=society,
        role="guard",
        status="approved"
    ).select_related("user").order_by("user__username")
    
    shifts = GuardShift.objects.filter(
        society=society,
        date=filter_date,
        guard__role="guard"
    ).select_related("guard__user")
    
    shifts_by_guard = {shift.guard_id: shift for shift in shifts}
    
    data = []
    for guard in guards:
        shift = shifts_by_guard.get(guard.id)
        
        if shift:
            # ✅ DETECT LATE CHECK-IN
            is_late_checkin = False
            if shift.check_in and shift.start_time:
                shift_start_datetime = timezone.make_aware(
                    datetime.combine(filter_date, shift.start_time),
                    timezone=india_tz
                )
                check_in_aware = shift.check_in.astimezone(india_tz)
                time_diff_minutes = (check_in_aware - shift_start_datetime).total_seconds() / 60
                is_late_checkin = time_diff_minutes > 15
            
            # ✅ CALCULATE DURATION
            duration_str = None
            if shift.check_out and shift.check_in:
                duration = shift.check_out - shift.check_in
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            elif shift.check_in and not shift.check_out:
                now = timezone.now().astimezone(india_tz)
                duration = now - shift.check_in.astimezone(india_tz)
                hours = int(duration.total_seconds() / 3600)
                minutes = int((duration.total_seconds() % 3600) / 60)
                duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
            
            # ✅ DETERMINE STATUS
            if shift.attendance_override != 'auto':
                status = shift.attendance_override
            elif shift.check_in and not shift.check_out:
                status = 'on_duty'
            elif shift.check_out:
                status = 'completed'
            else:
                status = 'absent'

            check_in_time = shift.check_in.astimezone(india_tz).strftime("%I:%M %p") if shift.check_in else "—"
            check_out_time = shift.check_out.astimezone(india_tz).strftime("%I:%M %p") if shift.check_out else "—"
            shift_time = f"{shift.start_time.strftime('%I:%M %p')} - {shift.end_time.strftime('%I:%M %p')}"
            
            data.append({
                "guard_profile_id": guard.id,
                "guard_name": guard.user.get_full_name() or guard.user.username,
                "shift": shift.get_shift_type_display(),
                "shift_time": shift_time,
                "check_in": check_in_time,
                "check_out": check_out_time,
                "status": status,
                "shift_id": shift.id,
                "attendance_override": shift.attendance_override,
                "duration": duration_str,
                "is_late": is_late_checkin,  # ✅ Auto-calculated late
            })
        else:
            data.append({
                "guard_profile_id": guard.id,
                "guard_name": guard.user.get_full_name() or guard.user.username,
                "shift": None,
                "shift_time": "—",
                "check_in": "—",
                "check_out": "—",
                "status": "no_shift",
                "shift_id": None,
                "attendance_override": "auto",
                "duration": None,
                "is_late": False
            })
    
    return JsonResponse({
        "success": True,
        "attendance": data,
        "date": filter_date.strftime("%d %b %Y")
    })


@login_required
@role_required("guard_admin")
def export_attendance(request):
    """
    Export attendance data as CSV - Includes ALL guards (excluding guard_admin)
    """
    date_str = request.GET.get("date", timezone.now().date().isoformat())
    society = request.user.userprofile.society
    
    try:
        filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        filter_date = timezone.now().date()
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{filter_date}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Guard Name', 
        'Guard ID', 
        'Shift Type', 
        'Shift Time',
        'Check In', 
        'Check Out', 
        'Status',
        'Duration (Hours)'
    ])
    
    # Get ALL guards (excluding guard_admin)
    guards = UserProfile.objects.filter(
        society=society,
        role="guard",  # ✅ Only regular guards
        status="approved"
    ).select_related("user").order_by("user__username")
    
    # Get shifts for the date (only for regular guards)
    shifts = GuardShift.objects.filter(
        society=society,
        date=filter_date,
        guard__role="guard"  # ✅ Only regular guards
    ).select_related("guard__user")
    
    shifts_by_guard = {shift.guard_id: shift for shift in shifts}
    
    # Write data for ALL guards
    for guard in guards:
        shift = shifts_by_guard.get(guard.id)
        
        if shift:
            from utils.attendance import get_attendance_status
            status = get_attendance_status(shift).title()

            check_in = shift.check_in.strftime("%I:%M %p") if shift.check_in else "—"
            check_out = shift.check_out.strftime("%I:%M %p") if shift.check_out else "—"
            
            # Calculate duration
            duration = "—"
            if shift.check_in and shift.check_out:
                time_diff = shift.check_out - shift.check_in
                hours = time_diff.total_seconds() / 3600
                duration = f"{hours:.2f}"
            
            shift_time = f"{shift.start_time.strftime('%I:%M %p') if shift.start_time else '—'} - {shift.end_time.strftime('%I:%M %p') if shift.end_time else '—'}"
            
            writer.writerow([
                guard.user.get_full_name() or guard.user.username,
                f"GRD{guard.id:03d}",
                shift.get_shift_type_display(),
                shift_time,
                check_in,
                check_out,
                status,
                duration
            ])
        else:
            # Guard with no shift
            writer.writerow([
                guard.user.get_full_name() or guard.user.username,
                f"GRD{guard.id:03d}",
                "Not Assigned",
                "—",
                "—",
                "—",
                "No Shift",
                "—"
            ])
    
    return response

# ================= PATROL API ENDPOINTS =================

@login_required
@role_required("guard_admin")
def checkpoint_coverage_api(request):
    """
    Get checkpoint coverage data for today
    Shows which checkpoints have been scanned and how many times
    """
    society = request.user.userprofile.society
    today = timezone.now().date()
    
    # Get all active checkpoints
    checkpoints = Checkpoint.objects.filter(
        society=society,
        is_active=True
    ).order_by('checkpoint_type', 'order', 'name')
    
    coverage_data = []
    
    for checkpoint in checkpoints:
        # Get scans for this checkpoint today (only from regular guards)
        scans_today = CheckpointScan.objects.filter(
            checkpoint=checkpoint,
            patrol_round__guard__role="guard",  # Only regular guards
            scanned_at__date=today
        )
        
        scan_count = scans_today.count()
        scanned_today = scan_count > 0
        
        # Get last scan time
        last_scan = scans_today.order_by('-scanned_at').first()
        last_scan_time = last_scan.scanned_at.strftime("%I:%M %p") if last_scan else None
        
        coverage_data.append({
            "id": checkpoint.id,
            "name": checkpoint.name,
            "type": checkpoint.checkpoint_type,
            "icon": checkpoint.icon,
            "scanned_today": scanned_today,
            "scan_count": scan_count,
            "last_scan_time": last_scan_time
        })
    
    return JsonResponse({
        "success": True,
        "checkpoints": coverage_data
    })


@login_required
@role_required("guard_admin")
def recent_patrol_history_api(request):
    """
    Get recent completed patrol rounds
    Only includes patrols by regular guards
    """
    society = request.user.userprofile.society
    limit = int(request.GET.get('limit', 10))
    
    # Get recent completed patrols (only for regular guards)
    patrols = PatrolRound.objects.filter(
        society=society,
        status="completed",
        guard__role="guard"  # Only regular guards
    ).select_related("guard__user").order_by('-start_time')[:limit]
    
    patrol_data = []
    
    for patrol in patrols:
        # Calculate duration
        if patrol.end_time and patrol.start_time:
            duration = patrol.end_time - patrol.start_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        else:
            duration_str = "N/A"
        
        # Calculate completion percentage
        completion = int((patrol.checkpoints_completed / patrol.total_checkpoints * 100)) if patrol.total_checkpoints > 0 else 0
        
        patrol_data.append({
            "id": patrol.id,
            "guard_name": patrol.guard.user.get_full_name() or patrol.guard.user.username,
            "date": patrol.start_time.strftime("%d %b %Y"),
            "start_time": patrol.start_time.strftime("%I:%M %p"),
            "end_time": patrol.end_time.strftime("%I:%M %p") if patrol.end_time else "—",
            "duration": duration_str,
            "checkpoints": patrol.checkpoints_completed,
            "total_checkpoints": patrol.total_checkpoints,
            "completion": completion,
            "notes": patrol.notes or ""
        })
    
    return JsonResponse({
        "success": True,
        "patrols": patrol_data
    })


@login_required
@role_required("guard_admin")
def patrol_detail(request, patrol_id):
    """
    Detailed view of a specific patrol round
    """
    patrol = get_object_or_404(
        PatrolRound.objects.select_related("guard__user"),
        id=patrol_id,
        society=request.user.userprofile.society,
        guard__role="guard"  # Only regular guards
    )
    
    # Get all checkpoint scans for this patrol
    scans = CheckpointScan.objects.filter(
        patrol_round=patrol
    ).select_related("checkpoint").order_by('scanned_at')
    
    # Get incidents reported during this patrol
    incidents = IncidentReport.objects.filter(
        patrol_round=patrol
    ).order_by('-reported_at')
    
    # Calculate stats
    if patrol.end_time and patrol.start_time:
        duration = patrol.end_time - patrol.start_time
        duration_minutes = int(duration.total_seconds() / 60)
    else:
        duration_minutes = 0
    
    context = {
        "patrol": patrol,
        "scans": scans,
        "incidents": incidents,
        "duration_minutes": duration_minutes,
        "completion_rate": int((patrol.checkpoints_completed / patrol.total_checkpoints * 100)) if patrol.total_checkpoints > 0 else 0
    }
    
    return render(request, "society_guard/patrol_detail.html", context)


@login_required
@role_required("guard_admin")
def patrol_history(request):
    """
    Complete patrol history with filters
    Only shows patrols by regular guards
    """
    society = request.user.userprofile.society
    
    # Date range filter
    days = int(request.GET.get("days", 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Guard filter
    guard_id = request.GET.get("guard")
    
    # Status filter
    status = request.GET.get("status", "all")
    
    # Base query (only regular guards)
    patrols = PatrolRound.objects.filter(
        society=society,
        start_time__date__range=[start_date, end_date],
        guard__role="guard"  # Only regular guards
    ).select_related("guard__user").order_by('-start_time')
    
    if guard_id:
        patrols = patrols.filter(guard_id=guard_id)
    
    if status != "all":
        patrols = patrols.filter(status=status)
    
    # Calculate stats
    total_patrols = patrols.count()
    completed_patrols = patrols.filter(status="completed").count()
    active_patrols = patrols.filter(status="active").count()
    
    # Average completion rate
    completed_with_checkpoints = patrols.filter(
        status="completed",
        total_checkpoints__gt=0
    )
    
    if completed_with_checkpoints.exists():
        avg_completion = sum(
            (p.checkpoints_completed / p.total_checkpoints * 100) 
            for p in completed_with_checkpoints
        ) / completed_with_checkpoints.count()
    else:
        avg_completion = 0
    
    # Get all guards for filter (only regular guards)
    all_guards = UserProfile.objects.filter(
        society=society,
        role="guard",  # Only regular guards
        status="approved"
    ).select_related("user")
    
    context = {
        "patrols": patrols,
        "start_date": start_date,
        "end_date": end_date,
        "total_patrols": total_patrols,
        "completed_patrols": completed_patrols,
        "active_patrols": active_patrols,
        "avg_completion": int(avg_completion),
        "all_guards": all_guards,
        "selected_guard": guard_id,
        "selected_status": status,
        "days_filter": days
    }
    
    return render(request, "society_guard/patrol_history.html", context)


@login_required
@role_required("guard_admin")
def patrol_stats_api(request):
    """
    Get patrol statistics for different time periods
    Only includes data from regular guards
    """
    society = request.user.userprofile.society
    period = request.GET.get('period', 'today')
    
    # Determine date range
    now = timezone.now()
    today = now.date()
    
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif period == 'month':
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    else:
        start_date = today
        end_date = today
    
    # Get patrols for period (only regular guards)
    patrols = PatrolRound.objects.filter(
        society=society,
        start_time__date__range=[start_date, end_date],
        guard__role="guard"  # Only regular guards
    )
    
    completed = patrols.filter(status="completed")
    
    # Calculate stats
    total_patrols = completed.count()
    
    total_checkpoints = sum(p.checkpoints_completed for p in completed)
    
    total_incidents = IncidentReport.objects.filter(
        society=society,
        reported_at__date__range=[start_date, end_date],
        reported_by__userprofile__role="guard"  # Only regular guards
    ).count()
    
    # Average duration
    if completed.exists():
        total_duration = sum(
            (p.end_time - p.start_time).total_seconds() / 60 
            for p in completed 
            if p.end_time
        )
        avg_duration = int(total_duration / completed.count()) if total_duration > 0 else 0
    else:
        avg_duration = 0
    
    return JsonResponse({
        "success": True,
        "period": period,
        "stats": {
            "total_patrols": total_patrols,
            "total_checkpoints": total_checkpoints,
            "total_incidents": total_incidents,
            "avg_duration_minutes": avg_duration
        }
    })

@login_required
@role_required("guard_admin")
def patrol_status_api(request):
    """
    Get real-time patrol status - AJAX endpoint for live updates
    Enhanced with MyGate-like features
    """
    society = request.user.userprofile.society
    
    # Only get patrols for regular guards
    active_patrols = PatrolRound.objects.filter(
        society=society,
        status="active",
        guard__role="guard"  # ✅ Only regular guards
    ).select_related("guard__user")
    
    patrols_data = []
    
    for patrol in active_patrols:
        # Calculate progress
        if patrol.total_checkpoints > 0:
            progress = int((patrol.checkpoints_completed / patrol.total_checkpoints) * 100)
        else:
            progress = 0
        
        # Calculate elapsed time
        elapsed = timezone.now() - patrol.start_time
        elapsed_minutes = int(elapsed.total_seconds() / 60)
        
        # Get completed checkpoints with details
        completed_scans = CheckpointScan.objects.filter(
            patrol_round=patrol
        ).select_related("checkpoint").order_by('-scanned_at')[:5]
        
        checkpoints = [
            {
                "name": scan.checkpoint.name,
                "type": scan.checkpoint.get_checkpoint_type_display(),
                "time": scan.scanned_at.strftime("%I:%M %p"),
                "notes": scan.notes or ""
            }
            for scan in completed_scans
        ]
        
        # Get guard initials
        guard_name = patrol.guard.user.get_full_name() or patrol.guard.user.username
        initials = "".join([n[0] for n in guard_name.split()[:2]]).upper()
        
        # Calculate estimated completion time
        if patrol.checkpoints_completed > 0 and elapsed_minutes > 0:
            avg_time_per_checkpoint = elapsed_minutes / patrol.checkpoints_completed
            remaining_checkpoints = patrol.total_checkpoints - patrol.checkpoints_completed
            est_remaining_minutes = int(avg_time_per_checkpoint * remaining_checkpoints)
        else:
            est_remaining_minutes = None
        
        patrols_data.append({
            "id": patrol.id,
            "guard": guard_name,
            "guard_initials": initials,
            "started_at": patrol.start_time.strftime("%I:%M %p"),
            "elapsed_minutes": elapsed_minutes,
            "completed": patrol.checkpoints_completed,
            "total": patrol.total_checkpoints,
            "progress": progress,
            "checkpoints": checkpoints,
            "est_remaining_minutes": est_remaining_minutes,
            "notes": patrol.notes or ""
        })
    
    # Today's stats (only for regular guards)
    today = timezone.now().date()
    
    completed_today = PatrolRound.objects.filter(
        society=society,
        status="completed",
        start_time__date=today,
        guard__role="guard"  # ✅ Only regular guards
    ).count()
    
    total_checkpoints_today = CheckpointScan.objects.filter(
        patrol_round__society=society,
        patrol_round__guard__role="guard",  # ✅ Only regular guards
        patrol_round__start_time__date=today
    ).count()
    
    total_checkpoints_possible = Checkpoint.objects.filter(
        society=society,
        is_active=True
    ).count() * completed_today if completed_today > 0 else 0
    
    incidents_today = IncidentReport.objects.filter(
        society=society,
        reported_at__date=today,
        reported_by__userprofile__role="guard"  # ✅ Only regular guards
    ).count()
    
    # Calculate average patrol duration today
    completed_patrols_today = PatrolRound.objects.filter(
        society=society,
        status="completed",
        start_time__date=today,
        guard__role="guard"  # ✅ Only regular guards
    )
    
    if completed_patrols_today.exists():
        total_duration = sum(
            (p.end_time - p.start_time).total_seconds() / 60 
            for p in completed_patrols_today 
            if p.end_time
        )
        avg_duration = int(total_duration / completed_patrols_today.count())
    else:
        avg_duration = 0
    
    return JsonResponse({
        "success": True,
        "active_patrols": patrols_data,
        "stats": {
            "completed_today": completed_today,
            "checkpoints_completed": total_checkpoints_today,
            "checkpoints_total": total_checkpoints_possible or total_checkpoints_today,
            "incidents": incidents_today,
            "avg_duration_minutes": avg_duration
        }
    })



@login_required
@role_required("guard_admin")
def view_shift_history(request):
    """
    View shift history/reports with filtering options
    Only shows regular guards (excludes guard_admin)
    """
    society = request.user.userprofile.society
    
    # Date range filter
    days = int(request.GET.get("days", 7))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Guard filter
    guard_id = request.GET.get("guard")
    
    # Only get shifts for regular guards
    shifts = GuardShift.objects.filter(
        society=society,
        date__range=[start_date, end_date],
        guard__role="guard"  # ✅ Only regular guards
    ).select_related("guard__user").order_by("-date", "shift_type")
    
    if guard_id:
        shifts = shifts.filter(guard_id=guard_id)
    
    # Calculate stats (only for regular guards)
    total_shifts = shifts.count()
    completed_shifts = shifts.filter(
        Q(check_out__isnull=False) | Q(attendance_override='present')
    ).count()
    missed_shifts = shifts.filter(
        Q(check_in__isnull=True) & Q(attendance_override__in=['auto', 'absent'])
    ).count()
    active_shifts = shifts.filter(
        check_in__isnull=False,
        check_out__isnull=True
    ).count()
    
    # Get all guards for filter dropdown (only regular guards)
    all_guards = UserProfile.objects.filter(
        society=society,
        role="guard",  # ✅ Only regular guards
        status="approved"
    ).select_related("user")
    
    context = {
        "shifts": shifts,
        "start_date": start_date,
        "end_date": end_date,
        "total_shifts": total_shifts,
        "completed_shifts": completed_shifts,
        "missed_shifts": missed_shifts,
        "active_shifts": active_shifts,
        "attendance_rate": int((completed_shifts / total_shifts * 100)) if total_shifts > 0 else 0,
        "all_guards": all_guards,
        "selected_guard": guard_id,
        "days_filter": days
    }
    
    return render(request, "society_guard/shift_reports.html", context)





@login_required
@role_required("guard_admin")
def generate_weekly_schedule(request):
    """
    Auto-generate weekly schedule with guard rotation
    Only creates shifts for regular guards (excludes guard_admin)
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    
    society = request.user.userprofile.society
    
    # Get all active regular guards only
    guards = list(UserProfile.objects.filter(
        society=society,
        role="guard",  # ✅ Only regular guards
        status="approved"
    ))
    
    if len(guards) < 3:
        return JsonResponse({
            "success": False,
            "error": "Need at least 3 guards for rotation"
        }, status=400)
    
    # Generate for next 7 days
    start_date = timezone.now().date() + timedelta(days=1)
    shifts_created = 0
    
    # Shift times
    shift_times = {
        "morning": (datetime.strptime("06:00:00", "%H:%M:%S").time(), 
                   datetime.strptime("14:00:00", "%H:%M:%S").time()),
        "afternoon": (datetime.strptime("14:00:00", "%H:%M:%S").time(), 
                     datetime.strptime("22:00:00", "%H:%M:%S").time()),
        "night": (datetime.strptime("22:00:00", "%H:%M:%S").time(), 
                 datetime.strptime("06:00:00", "%H:%M:%S").time()),
    }
    
    for day_offset in range(7):
        date = start_date + timedelta(days=day_offset)
        
        # Rotate guards through shifts
        morning_guard = guards[day_offset % len(guards)]
        afternoon_guard = guards[(day_offset + 1) % len(guards)]
        night_guard = guards[(day_offset + 2) % len(guards)]
        
        # Create shifts
        for shift_type, guard in [
            ("morning", morning_guard),
            ("afternoon", afternoon_guard),
            ("night", night_guard)
        ]:
            start_time, end_time = shift_times[shift_type]
            
            shift, created = GuardShift.objects.get_or_create(
                guard=guard,
                society=society,
                date=date,
                shift_type=shift_type,
                defaults={
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )
            if created:
                shifts_created += 1
    
    return JsonResponse({
        "success": True,
        "message": f"Created {shifts_created} shifts for next 7 days"
    })




@login_required
@role_required("guard_admin")
def guard_attendance(request):
    society = request.user.userprofile.society
    date = request.GET.get("date")

    shifts = GuardShift.objects.filter(
        society=society,
        date=date
    ).select_related("guard", "guard__user")

    return render(request, "partials/attendance_rows.html", {
        "shifts": shifts
    })




@require_POST
def call_resident(request, visitor_id):
    """
    Send notification to resident for visitor approval
    AJAX endpoint called from dashboard
    """
    try:
        visitor = Visitor.objects.select_related('apartment').get(id=visitor_id)
        
        # Get all residents of the apartment
        residents = UserProfile.objects.filter(
            apartment=visitor.apartment,
            role='resident',
            status='approved'
        ).select_related('user')
        
        if not residents.exists():
            return JsonResponse({
                'success': False,
                'error': 'No residents found for this apartment'
            }, status=404)
        
        # Create notification for each resident
        notifications_created = 0
        for resident_profile in residents:
            Notification.objects.create(
                user=resident_profile.user,
                sender=request.user,
                title=f"Visitor Approval Required",
                message=f"{visitor.name} ({visitor.get_visitor_type_display()}) is waiting at the gate. Purpose: {visitor.purpose or 'Visit'}. Mobile: {visitor.mobile}",
                visitor=visitor
            )
            notifications_created += 1
        
        return JsonResponse({
            'success': True,
            'message': f'Notification sent to {notifications_created} resident(s)',
            'visitor_id': visitor_id
        })
        
    except Visitor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Visitor not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@role_required("guard", "guard_admin")
def guard_notifications(request):
    from django.db.models import Q
    from .models import Notification, LeaveRequest, UserProfile

    profile = request.user.userprofile
    society = profile.society

    # ── Notifications ──────────────────────────────────────────
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count  = notifications.filter(is_read=False).count()
    notifications.filter(is_read=False).update(is_read=True)

    # ── Leave Requests (guard_admin only) ──────────────────────
    pending_leaves  = []
    approved_leaves = []
    rejected_leaves = []
    pending_count   = 0

    if profile.role == "guard_admin":
        pending_leaves  = LeaveRequest.objects.filter(
            society=society, 
            status='pending'
        ).select_related('guard__user').order_by('-applied_at')

        approved_leaves = LeaveRequest.objects.filter(
            society=society, 
            status='approved'
        ).select_related('guard__user').order_by('-reviewed_at')

        rejected_leaves = LeaveRequest.objects.filter(
            society=society, 
            status='rejected'
        ).select_related('guard__user').order_by('-reviewed_at')

        pending_count = pending_leaves.count()


    return render(request, "society_guard/guard_notifications.html", {
        "notifications":   notifications,
        "unread_count":    unread_count,
        "pending_leaves":  pending_leaves,
        "approved_leaves": approved_leaves,
        "rejected_leaves": rejected_leaves,
        "pending_count":   pending_count,
        "is_guard_admin":  profile.role == "guard_admin",
    })

@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_reply_to_notification(request, notification_id):
    try:
        notification = Notification.objects.select_related(
            "sender", "parent"
        ).get(id=notification_id, user=request.user)

        message = request.POST.get("message", "").strip()
        if not message:
            return JsonResponse({"success": False})

        # 🔥 Find root notification
        root = notification
        while root.parent:
            root = root.parent

        resident_user = root.user  # original resident

        Notification.objects.create(
            user=resident_user,      # send back to resident
            sender=request.user,     # guard
            parent=root,             # same thread
            title="💬 Reply from Guard",
            message=message
        )

        return JsonResponse({"success": True})

    except Notification.DoesNotExist:
        return JsonResponse({"success": False}, status=404)


@login_required
@role_required("guard", "guard_admin")

def guard_profile(request):
    user = request.user
    profile = user.userprofile

    visitors_count = Visitor.objects.filter(
        checked_in_by=user
    ).count()

    deliveries_count = Delivery.objects.filter(
        received_by=user
    ).count() if hasattr(Delivery, "received_by") else 0

    posts_count = CommunityPost.objects.filter(
        user=user
    ).count()

    active_services_count = 0  # Guards don't have services

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        "profile": profile,
        "user_form": user_form,
        "profile_form": profile_form,
        "visitors_count": visitors_count,
        "deliveries_count": deliveries_count,
        "posts_count": posts_count,
        "active_services_count": active_services_count,
    }

    return render(request, "society_guard/guard_profile.html", context)



@login_required
@role_required("guard", "guard_admin")

def guard_entry(request):
    profile = request.user.userprofile
    society = profile.society

    entry_type = request.GET.get('type', 'visitor')

    if request.method == "POST":
        entry_type = request.POST.get('entry_type', 'visitor')

        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        apartment_id = request.POST.get('apartment')

        try:
            apartment = Apartment.objects.get(id=apartment_id, society=society)

            if entry_type == 'visitor':
                visitor = Visitor.objects.create(
                    society=society,
                    apartment=apartment,
                    name=name,
                    mobile=mobile,
                    visitor_type='guest',
                    purpose=request.POST.get('purpose', ''),
                    status='pending',   # ✅ CHANGE HERE
                    checked_in_by=request.user
                )

                # Save photo
                photo = request.FILES.get("photo")
                if photo:
                    VisitorPhoto.objects.create(
                        visitor=visitor,
                        photo=photo,
                        taken_by=request.user
                    )

                messages.success(request, f"✓ Visitor {name} request sent to resident for approval")

            return redirect('guard_entry')

        except Apartment.DoesNotExist:
            messages.error(request, "Invalid apartment selected")

    apartments = Apartment.objects.filter(society=society).order_by('block', 'flat_number')

    # ✅ RECENT ENTRIES = REAL ENTRIES ONLY
    recent_entries = Visitor.objects.filter(
        society=society,
        status__in=["checked_in", "checked_out"],
        check_in_time__date=timezone.now().date()
    ).prefetch_related("photos").order_by('-check_in_time')[:5]


    return render(request, 'society_guard/guard_entry.html', {
        'entry_type': entry_type,
        'apartments': apartments,
        'recent_entries': recent_entries,
    })


@login_required
@role_required("guard", "guard_admin")

def guard_visitors(request):
    """
    Guard Visitors Management Page
    """
    profile = request.user.userprofile
    society = profile.society
    today = timezone.now().date()
    
    # Pending visitors
    pending_visitors = Visitor.objects.filter(
        society=society,
        status="pending"
    ).select_related('apartment').order_by('-created_at')
    
    # Active visitors (checked in)
    active_visitors = Visitor.objects.filter(
        society=society,
        status="checked_in"
    ).select_related('apartment').order_by('-created_at')
    
    # History (checked out)
    history_visitors = Visitor.objects.filter(
        society=society,
        status="checked_out"
    ).select_related('apartment').order_by('-created_at')[:50]
    
    # Counts
    pending_count = pending_visitors.count()
    active_count = active_visitors.count()
    today_total = Visitor.objects.filter(
        society=society,
        created_at__date=today
    ).count()
    
    context = {
        'pending_visitors': pending_visitors,
        'active_visitors': active_visitors,
        'history_visitors': history_visitors,
        'pending_count': pending_count,
        'active_count': active_count,
        'today_total': today_total,
    }
    
    return render(request, 'society_guard/guard_visitors.html', context)


@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_approve_visitor(request, visitor_id):
    """
    Guard approves a visitor (bypassing resident approval if needed)
    """
    profile = request.user.userprofile
    society = profile.society
    
    try:
        visitor = Visitor.objects.get(
            id=visitor_id,
            society=society,
            status="pending"
        )
        
        visitor.status = "checked_in"
        visitor.save()
        
        # Create notification
        Notification.objects.create(
            user=visitor.apartment.residents.first(),
            sender=request.user,
            visitor=visitor,  # ✅ REQUIRED
            title="🟢 Visitor Checked In",
            message=f"{visitor.name} checked in by guard"
        )

        
        messages.success(request, f"✓ {visitor.name} checked in successfully")
        
    except Visitor.DoesNotExist:
        messages.error(request, "Visitor not found")
    
    return redirect('guard_visitors')

@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_verify_visitor_code(request):
    """
    Guard verifies visitor entry code
    Returns visitor details if valid
    """
    import json
    
    # Parse JSON body
    try:
        data = json.loads(request.body)
        code = data.get("entry_code", "").strip()
    except:
        code = request.POST.get("entry_code", "").strip()

    # Validate code length
    if len(code) != 6:
        return JsonResponse({
            "success": False,
            "error": "❌ Invalid code format. Must be 6 digits."
        })

    # Find visitor with this code
    visitor = Visitor.objects.filter(
        entry_code=code,
        status="approved",  # Only approved visitors can check in
        society=request.user.userprofile.society
    ).select_related("apartment").first()


    # Get visitor photo (first photo)
    photo = visitor.photos.first() if visitor else None
    photo_url = photo.photo.url if photo and photo.photo else None

    if not visitor:
        return JsonResponse({
            "success": False,
            "error": "❌ Invalid or expired entry code. Visitor may have already checked in or code is incorrect."
        })

    # Check if expected time has passed (optional validation)
    if visitor.expected_at and visitor.expected_at < timezone.now():
        hours_late = (timezone.now() - visitor.expected_at).total_seconds() / 3600
        if hours_late > 24:  # More than 24 hours late
            return JsonResponse({
                "success": False,
                "error": f"⚠️ This code expired {int(hours_late)} hours ago. Please contact resident for new approval."
            })

    # Return visitor details
    return JsonResponse({
        "success": True,
        "visitor": {
            "id": visitor.id,
            "name": visitor.name,
            "mobile": visitor.mobile,
            "apartment": f"{visitor.apartment.block}-{visitor.apartment.flat_number}",
            "purpose": visitor.purpose or "Visit",
            "expected_at": visitor.expected_at.strftime("%d %b %Y, %I:%M %p") if visitor.expected_at else "Not specified",
            "visitor_type": visitor.get_visitor_type_display(),
            "photo_url": photo_url, 
        }
    })



@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_checkout_visitor(request, visitor_id):
    """
    Guard checks out visitor
    Records check-out time and calculates duration
    """
    try:
        visitor = get_object_or_404(
            Visitor,
            id=visitor_id,
            society=request.user.userprofile.society,
            status="checked_in"
        )

        # Calculate duration
        if visitor.check_in_time:
            duration = timezone.now() - visitor.check_in_time
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        else:
            duration_str = "Unknown"

        # Update visitor status
        visitor.status = "checked_out"
        visitor.check_out_time = timezone.now()
        visitor.checked_out_by = request.user
        visitor.save()

        # Notify resident
        Notification.objects.create(
            user=visitor.apartment.userprofile_set.first().user,
            sender=request.user,
            visitor=visitor,  # ✅ REQUIRED
            title="🔴 Visitor Checked Out",
            message=f"{visitor.name} checked out at {visitor.check_out_time.strftime('%I:%M %p')}"
        )


        messages.success(
            request,
            f"✅ {visitor.name} checked out successfully. Visit duration: {duration_str}"
        )

    except Visitor.DoesNotExist:
        messages.error(request, "❌ Visitor not found or not checked in")

    return redirect("guard_visitors")



@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_checkin_visitor(request, visitor_id):
    """
    Guard checks in visitor using verified entry code
    Records check-in time and guard info (IST time)
    """
    try:
        visitor = get_object_or_404(
            Visitor,
            id=visitor_id,
            status="approved",
            society=request.user.userprofile.society
        )

        # ✅ Get current IST time
        ist_time = timezone.now().astimezone(ZoneInfo("Asia/Kolkata"))

        # Update visitor status
        visitor.status = "checked_in"
        visitor.check_in_time = ist_time
        visitor.checked_in_by = request.user
        visitor.entry_code = None  # Invalidate code after use
        visitor.save()

        # Notify resident
        Notification.objects.create(
            user=visitor.apartment.userprofile_set.first().user,
            sender=request.user,
            visitor=visitor,
            title="🟢 Visitor Checked In",
            message=f"{visitor.name} has checked in at {ist_time.strftime('%I:%M %p')}"
        )

        messages.success(
            request,
            f"✅ {visitor.name} checked in successfully at {ist_time.strftime('%I:%M %p')}"
        )

    except Visitor.DoesNotExist:
        messages.error(request, "❌ Visitor not found or already checked in")

    return redirect("guard_visitors")

import pytz
from datetime import datetime, time as dt_time
from django.utils import timezone

@login_required
@role_required("guard", "guard_admin")
@require_POST
def guard_check_in(request):
    """
    Guard checks in for their assigned shift (IST timezone)
    - Allows check-in only 10 minutes before shift start
    - Blocks after shift end
    - Auto-detects late check-ins (15 min rule)
    """

    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    today = now.date()

    profile = request.user.userprofile
    society = profile.society

    # 🔹 Get assigned shift (DO NOT auto-create)
    shift = GuardShift.objects.filter(
        guard=profile,
        society=society,
        date=today
    ).first()

    if not shift:
        return JsonResponse({
            "success": False,
            "error": "No shift assigned for today."
        })

    # 🔹 Already checked in
    if shift.check_in:
        return JsonResponse({
            "success": False,
            "error": f"Already checked in at {shift.check_in.strftime('%I:%M %p')}"
        })

    # ================= BUILD SHIFT DATETIME =================

    shift_start_date = today

    # Handle night shift (22:00 – 06:00)
    if shift.shift_type == "night" and shift.end_time < shift.start_time:
        if now.time() < shift.start_time:
            shift_start_date = today - timedelta(days=1)

    shift_start_datetime = timezone.make_aware(
        datetime.combine(shift_start_date, shift.start_time),
        timezone=india_tz
    )

    shift_end_datetime = timezone.make_aware(
        datetime.combine(shift_start_date, shift.end_time),
        timezone=india_tz
    )

    # If end crosses midnight
    if shift_end_datetime <= shift_start_datetime:
        shift_end_datetime += timedelta(days=1)

    # ================= CHECK-IN WINDOW CONTROL =================

    checkin_open_time = shift_start_datetime - timedelta(minutes=10)

    if now < checkin_open_time:
        minutes_remaining = int((checkin_open_time - now).total_seconds() / 60)
        return JsonResponse({
            "success": False,
            "error": f"Check-in opens in {minutes_remaining} minutes."
        })

    if now > shift_end_datetime:
        return JsonResponse({
            "success": False,
            "error": "Shift has already ended. Check-in not allowed."
        })

    # ================= RECORD CHECK-IN =================

    shift.check_in = now
    shift.status = "active"
    shift.is_present = True

    # ================= AUTO-DETECT LATE =================

    time_diff_minutes = (now - shift_start_datetime).total_seconds() / 60

    if shift.attendance_override == "auto":
        if time_diff_minutes > 15:
            shift.attendance_override = "late"
            shift.attendance_marked_by = request.user
            shift.attendance_marked_at = now
            is_late = True
            late_by_minutes = int(time_diff_minutes)
        else:
            shift.attendance_override = "present"
            is_late = False
            late_by_minutes = 0
    else:
        is_late = shift.attendance_override == "late"
        late_by_minutes = 0

    shift.save()

    # ================= RESPONSE MESSAGE =================

    message = f"Checked in at {now.strftime('%I:%M %p')}"
    if is_late:
        hours = late_by_minutes // 60
        minutes = late_by_minutes % 60
        late_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        message += f" (Late by {late_str})"

    return JsonResponse({
        "success": True,
        "message": message,
        "check_in_time": now.strftime('%I:%M %p'),
        "shift_type": shift.get_shift_type_display(),
        "is_late": is_late,
        "late_by_minutes": late_by_minutes if is_late else None
    })



@login_required
@role_required("guard", "guard_admin")
@require_POST
def guard_check_out(request):
    """
    Guard checks out from their shift (IST timezone)
    """
    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    today = now.date()
    
    profile = request.user.userprofile
    society = profile.society
    
    # Find active shift
    shift = GuardShift.objects.filter(
        guard=profile,
        society=society,
        date=today,
        check_in__isnull=False,
        check_out__isnull=True
    ).first()
    
    if not shift:
        return JsonResponse({
            "success": False,
            "error": "No active shift found. Please check in first."
        })
    
    # Record check-out (IST timezone)
    shift.check_out = now
    shift.status = "completed"
    shift.save()
    
    # Calculate duration
    duration = now - shift.check_in
    hours = int(duration.total_seconds() / 3600)
    minutes = int((duration.total_seconds() % 3600) / 60)
    duration_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
    
    return JsonResponse({
        "success": True,
        "message": f"Checked out at {now.strftime('%I:%M %p')}",
        "check_out_time": now.strftime('%I:%M %p'),
        "duration": duration_str
    })


@login_required
@role_required("guard", "guard_admin")
def get_shift_status(request):
    """
    Get current shift status for the guard (IST timezone)
    Used for real-time updates
    """

    india_tz = pytz.timezone("Asia/Kolkata")
    now = timezone.now().astimezone(india_tz)
    today = now.date()

    profile = request.user.userprofile
    society = profile.society

    shift = GuardShift.objects.filter(
        guard=profile,
        society=society,
        date=today
    ).first()

    if not shift:
        return JsonResponse({
            "has_shift": False,
            "checked_in": False,
            "is_checkin_allowed": False
        })

    # ================= BUILD SHIFT DATETIME =================

    shift_start_date = today

    if shift.shift_type == "night" and shift.end_time < shift.start_time:
        if now.time() < shift.start_time:
            shift_start_date = today - timedelta(days=1)

    shift_start_datetime = timezone.make_aware(
        datetime.combine(shift_start_date, shift.start_time),
        timezone=india_tz
    )

    shift_end_datetime = timezone.make_aware(
        datetime.combine(shift_start_date, shift.end_time),
        timezone=india_tz
    )

    if shift_end_datetime <= shift_start_datetime:
        shift_end_datetime += timedelta(days=1)

    checkin_open_time = shift_start_datetime - timedelta(minutes=10)

    is_checkin_allowed = (
        checkin_open_time <= now <= shift_end_datetime
        and shift.check_in is None
    )

    # ================= LATE STATUS =================

    is_late = shift.attendance_override == "late"

    return JsonResponse({
        "has_shift": True,
        "checked_in": shift.check_in is not None,
        "checked_out": shift.check_out is not None,
        "check_in_time": shift.check_in.astimezone(india_tz).strftime('%I:%M %p') if shift.check_in else None,
        "check_out_time": shift.check_out.astimezone(india_tz).strftime('%I:%M %p') if shift.check_out else None,
        "shift_type": shift.get_shift_type_display(),
        "status": shift.status,
        "is_late": is_late,
        "attendance_override": shift.attendance_override,
        "is_checkin_allowed": is_checkin_allowed
    })


@login_required
@role_required("guard", "guard_admin")

def guard_parcels(request):
    """
    Guard Parcel Management Page
    """
    profile = request.user.userprofile
    society = profile.society
    today = timezone.now().date()
    
    if request.method == "POST":
        # Handle new parcel entry
        apartment_id = request.POST.get('apartment')
        company = request.POST.get('company')
        tracking_id = request.POST.get('tracking_id', '')
        
        try:
            apartment = Apartment.objects.get(id=apartment_id, society=society)
            
            # Generate OTP
            otp = str(timezone.now().timestamp())[-6:]
            
            Delivery.objects.create(
                apartment=apartment,
                company=company,
                tracking_id=tracking_id,
                otp=otp,
                status='pending',
                received_at=timezone.now()
            )
            
            messages.success(request, f"✓ Parcel logged. OTP: {otp}")
            
            # Notify resident
            # TODO: Send SMS/notification with OTP
            
            return redirect('guard_parcels')
            
        except Apartment.DoesNotExist:
            messages.error(request, "Invalid apartment")
    
    # Get deliveries
    pending_deliveries = Delivery.objects.filter(
        apartment__society=society,
        status__iexact='pending'
    ).select_related('apartment').order_by('-received_at')
    
    delivered_deliveries = Delivery.objects.filter(
        apartment__society=society,
        status__iexact='received',
        received_at__date=today
    ).select_related('apartment').order_by('-received_at')
    
    # Stats
    today_parcels = Delivery.objects.filter(
        apartment__society=society,
        received_at__date=today
    ).count()
    
    pending_parcels = pending_deliveries.count()
    delivered_parcels = delivered_deliveries.count()
    
    # Get apartments for form
    apartments = Apartment.objects.filter(society=society).order_by('block', 'flat_number')
    
    context = {
        'pending_deliveries': pending_deliveries,
        'delivered_deliveries': delivered_deliveries,
        'today_parcels': today_parcels,
        'pending_parcels': pending_parcels,
        'delivered_parcels': delivered_parcels,
        'apartments': apartments,
    }
    
    return render(request, 'society_guard/guard_parcels.html', context)

@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_notify_parcel(request, delivery_id):
    profile = request.user.userprofile
    society = profile.society

    try:
        delivery = Delivery.objects.select_related(
            "apartment"
        ).get(
            id=delivery_id,
            apartment__society=society,
            status__iexact="pending"
        )

        # 🔥 Get all residents of that apartment
        residents = UserProfile.objects.filter(
            apartment=delivery.apartment,
            role="resident",
            status="approved"
        ).select_related("user")

        if not residents.exists():
            return JsonResponse({
                "success": False,
                "message": "No resident found for this flat"
            }, status=404)

        # 🔔 Create notification for each resident
        for resident in residents:
            Notification.objects.create(
                user=resident.user,        # receiver (resident)
                sender=request.user,       # sender (guard)
                title="📦 Parcel Arrived",
                message="Parcel arrived"
            )



        return JsonResponse({
            "success": True,
            "message": "Resident notified successfully"
        })

    except Delivery.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Parcel not found"
        }, status=404)

@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_deliver_parcel(request, delivery_id):
    """
    Mark parcel as delivered after OTP verification
    """
    profile = request.user.userprofile
    society = profile.society
    
    otp = request.POST.get('otp')
    
    try:
        delivery = Delivery.objects.get(
            id=delivery_id,
            apartment__society=society,
            otp=otp,
            status__iexact='pending'
        )
        
        delivery.status = 'received'
        delivery.save()
        
        messages.success(request, "✓ Parcel delivered successfully")
        
    except Delivery.DoesNotExist:
        messages.error(request, "Invalid OTP or parcel not found")
    
    return redirect('guard_parcels')


@login_required
@role_required("guard", "guard_admin")

def guard_patrol(request):
    profile = request.user.userprofile
    society = profile.society

    # ==================================================
    # ACTIVE PATROL
    # ==================================================
    patrol_round = PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="active"
    ).first()

    patrol_active = patrol_round is not None
    patrol_start_time = patrol_round.start_time if patrol_round else None

    # ==================================================
    # CHECKPOINTS (ALL REGISTERED FOR SOCIETY)
    # ==================================================
    checkpoints_qs = Checkpoint.objects.filter(
        society=society,
        is_active=True
    ).order_by("order", "name")

    # ==================================================
    # CHECKPOINT SCANS (ONLY FOR ACTIVE PATROL)
    # ==================================================
    scan_map = {}
    if patrol_round:
        scans = CheckpointScan.objects.filter(
            patrol_round=patrol_round
        )
        scan_map = {scan.checkpoint_id: scan.scanned_at for scan in scans}

    # ==================================================
    # PREPARE CHECKPOINT DATA FOR TEMPLATE
    # ==================================================
    checkpoints = []
    for cp in checkpoints_qs:
        checkpoints.append({
            "id": cp.id,
            "name": cp.name,
            "icon": cp.icon,
            "type": cp.checkpoint_type,
            "completed": cp.id in scan_map,
            "completed_at": scan_map.get(cp.id),
        })

    # ==================================================
    # TYPE-WISE TOTAL COUNTS
    # ==================================================
    gate_total = sum(1 for c in checkpoints if c["type"] == "gate")
    parking_total = sum(1 for c in checkpoints if c["type"] == "parking")
    amenity_total = sum(1 for c in checkpoints if c["type"] == "amenity")
    perimeter_total = sum(1 for c in checkpoints if c["type"] == "perimeter")
    building_total = sum(1 for c in checkpoints if c["type"] == "building")

    # ==================================================
    # TYPE-WISE COMPLETED COUNTS
    # ==================================================
    gates_checked = sum(1 for c in checkpoints if c["type"] == "gate" and c["completed"])
    parking_checked = sum(1 for c in checkpoints if c["type"] == "parking" and c["completed"])
    amenities_checked = sum(1 for c in checkpoints if c["type"] == "amenity" and c["completed"])
    perimeter_checked = sum(1 for c in checkpoints if c["type"] == "perimeter" and c["completed"])
    building_checked = sum(1 for c in checkpoints if c["type"] == "building" and c["completed"])

    # ==================================================
    # OVERALL STATS
    # ==================================================
    completed_checkpoints = sum(1 for c in checkpoints if c["completed"])
    total_checkpoints = len(checkpoints)

    # ==================================================
    # TODAY'S COMPLETED PATROL LOGS
    # ==================================================
    patrol_logs = PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="completed",
        start_time__date=timezone.localdate()
    ).order_by("-start_time")

    # ==================================================
    # CONTEXT
    # ==================================================
    context = {
        # Patrol state
        "patrol_active": patrol_active,
        "patrol_start_time": patrol_start_time,

        # Checkpoints
        "checkpoints": checkpoints,

        # Totals
        "gate_total": gate_total,
        "parking_total": parking_total,
        "amenity_total": amenity_total,
        "perimeter_total": perimeter_total,
        "building_total": building_total,

        # Completed
        "gates_checked": gates_checked,
        "parking_checked": parking_checked,
        "amenities_checked": amenities_checked,
        "perimeter_checked": perimeter_checked,
        "building_checked": building_checked,

        # Overall
        "completed_checkpoints": completed_checkpoints,
        "total_checkpoints": total_checkpoints,

        # History
        "patrol_logs": patrol_logs,
    }

    return render(request, "society_guard/guard_patrol.html", context)

@login_required
@role_required("guard", "guard_admin")

@require_POST
def start_patrol(request):
    profile = request.user.userprofile
    society = profile.society

    # Prevent multiple active patrols
    if PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="active"
    ).exists():
        return JsonResponse({"error": "Patrol already active"}, status=400)

    patrol = PatrolRound.objects.create(
        guard=profile,
        society=society,
        status="active",
        total_checkpoints=Checkpoint.objects.filter(
            society=society,
            is_active=True
        ).count()
    )

    return JsonResponse({"success": True, "patrol_id": patrol.id})

@login_required
@role_required("guard", "guard_admin")

@require_POST
def stop_patrol(request):
    profile = request.user.userprofile

    patrol = PatrolRound.objects.filter(
        guard=profile,
        status="active"
    ).first()

    if not patrol:
        return JsonResponse({"error": "No active patrol"}, status=400)

    patrol.end_time = timezone.now()
    patrol.status = "completed"
    patrol.checkpoints_completed = patrol.scans.count()
    patrol.save()

    return JsonResponse({"success": True})


@login_required
@role_required("guard", "guard_admin")

@require_POST
def mark_checkpoint(request):
    checkpoint_id = request.POST.get("checkpoint_id")

    profile = request.user.userprofile
    society = profile.society

    patrol = PatrolRound.objects.filter(
        guard=profile,
        society=society,
        status="active"
    ).first()

    if not patrol:
        return JsonResponse({"error": "No active patrol"}, status=400)

    checkpoint = Checkpoint.objects.filter(
        id=checkpoint_id,
        society=society,
        is_active=True
    ).first()

    if not checkpoint:
        return JsonResponse({"error": "Invalid checkpoint"}, status=400)

    # Prevent duplicate scan
    scan, created = CheckpointScan.objects.get_or_create(
        patrol_round=patrol,
        checkpoint=checkpoint
    )

    return JsonResponse({"success": True})


@login_required
@role_required("guard", "guard_admin")

def scan_checkpoint(request):
    checkpoint_id = request.POST.get("checkpoint_id")

    profile = request.user.userprofile
    patrol = get_object_or_404(
        PatrolRound,
        guard=profile,
        status='active'
    )

    checkpoint = get_object_or_404(
        Checkpoint,
        id=checkpoint_id,
        society=profile.society
    )

    scan, created = CheckpointScan.objects.get_or_create(
        patrol_round=patrol,
        checkpoint=checkpoint
    )

    if created:
        patrol.checkpoints_completed = patrol.scans.count()
        patrol.save()

    return JsonResponse({
        "success": True,
        "checkpoint": checkpoint.name,
        "time": scan.scanned_at.strftime("%I:%M %p")
    })
@login_required
@role_required("guard", "guard_admin")

def report_incident(request):
    IncidentReport.objects.create(
        society=request.user.userprofile.society,
        reported_by=request.user,
        incident_type=request.POST["type"],
        title=request.POST["title"],
        description=request.POST["description"],
        location=request.POST["location"]
    )

    return JsonResponse({"success": True})

@login_required
@role_required("guard", "guard_admin")

def mark_help_entry(request, help_id):
    """
    Mark daily help staff check-in
    Uses Indian timezone
    """
    india_tz = pytz.timezone('Asia/Kolkata')
    now_india = timezone.now().astimezone(india_tz)
    
    try:
        help_obj = DailyHelp.objects.get(id=help_id)
        
        # Check if already checked in today
        existing_attendance = DailyHelpAttendance.objects.filter(
            daily_help=help_obj,
            date=now_india.date(),
            check_out__isnull=True
        ).first()
        
        if existing_attendance:
            messages.warning(
                request,
                f"⚠️ {help_obj.name} is already checked in since {existing_attendance.check_in.strftime('%I:%M %p')}"
            )
        else:
            # Create new attendance record
            DailyHelpAttendance.objects.create(
                daily_help=help_obj,
                date=now_india.date(),
                check_in=now_india
            )
            
            messages.success(
                request, 
                f"✓ {help_obj.name} ({help_obj.service.name}) checked in at {now_india.strftime('%I:%M %p')}"
            )
        
    except DailyHelp.DoesNotExist:
        messages.error(request, "❌ Daily help not found")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect("guard_dashboard")

import uuid

@login_required
@role_required("guard_admin")
@require_POST
def add_checkpoint(request):
    profile = request.user.userprofile
    society = profile.society

    name = request.POST.get("name", "").strip()
    checkpoint_type = request.POST.get("checkpoint_type")

    if not name or not checkpoint_type:
        return JsonResponse({"error": "Invalid data"}, status=400)

    checkpoint = Checkpoint.objects.create(
        society=society,
        name=name,
        checkpoint_type=checkpoint_type,
        location_description="Added by guard",
        qr_code=uuid.uuid4().hex,  # ✅ IMPORTANT
        order=Checkpoint.objects.filter(society=society).count() + 1
    )

    return JsonResponse({"success": True})



@login_required
@role_required("guard", "guard_admin")

def mark_help_exit(request, help_id):
    """
    Mark daily help staff check-out
    Uses Indian timezone
    """
    india_tz = pytz.timezone('Asia/Kolkata')
    now_india = timezone.now().astimezone(india_tz)
    
    try:
        help_obj = DailyHelp.objects.get(id=help_id)
        
        # Find today's open attendance record
        attendance = DailyHelpAttendance.objects.filter(
            daily_help=help_obj,
            date=now_india.date(),
            check_out__isnull=True
        ).first()
        
        if attendance:
            attendance.check_out = now_india
            attendance.save()
            
            # Calculate duration
            duration = now_india - attendance.check_in
            hours = int(duration.total_seconds() / 3600)
            minutes = int((duration.total_seconds() % 3600) / 60)
            
            messages.success(
                request,
                f"✓ {help_obj.name} checked out at {now_india.strftime('%I:%M %p')}. Duration: {hours}h {minutes}m"
            )
        else:
            messages.warning(
                request,
                f"⚠️ No open check-in found for {help_obj.name} today. Please check them in first."
            )
            
    except DailyHelp.DoesNotExist:
        messages.error(request, "❌ Daily help not found")
    except Exception as e:
        messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect("guard_dashboard")

@login_required
@role_required("guard", "guard_admin")

def quick_visitor_checkin(request):
    """
    Quick check-in for pre-approved visitors using entry code
    """
    if request.method == 'POST':
        entry_code = request.POST.get('entry_code', '').strip()
        
        if not entry_code:
            messages.error(request, "❌ Please enter an entry code")
            return redirect("guard_dashboard")
        
        india_tz = pytz.timezone('Asia/Kolkata')
        now_india = timezone.now().astimezone(india_tz)
        
        try:
            # Find visitor with this entry code
            visitor = Visitor.objects.get(
            entry_code=entry_code,
            status='approved',
            society=request.user.userprofile.society,
            check_in_time__isnull=True
        )

            
            # Check in the visitor
            visitor.status = 'checked_in'
            visitor.check_in_time = now_india
            visitor.checked_in_by = request.user
            visitor.save()
            
            messages.success(
                request,
                f"✓ {visitor.name} checked in successfully at {now_india.strftime('%I:%M %p')}"
            )
            
        except Visitor.DoesNotExist:
            messages.error(
                request,
                "❌ Invalid entry code or visitor already checked in"
            )
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
    
    return redirect("guard_dashboard")

@login_required
@role_required("guard", "guard_admin")

def dashboard_stats_api(request):
    """
    API endpoint for real-time dashboard statistics
    Used for auto-refresh without full page reload
    """
    india_tz = pytz.timezone('Asia/Kolkata')
    now_india = timezone.now().astimezone(india_tz)
    today = now_india.date()
    
    profile = request.user.userprofile
    society = profile.society
    
    # Calculate stats
    today_entries = Visitor.objects.filter(
        society=society,
        check_in_time__date=today,
        status__in=['checked_in', 'checked_out']
    ).count()
    
    pending_count = Visitor.objects.filter(
        society=society,
        status="pending"
    ).count()
    
    parcels_today = Delivery.objects.filter(
        apartment__society=society,
        received_at__date=today
    ).count()
    
    return JsonResponse({
        'success': True,
        'stats': {
            'today_entries': today_entries,
            'pending_count': pending_count,
            'parcels_today': parcels_today,
            'current_time': now_india.strftime("%I:%M %p")
        }
    })

@login_required
@role_required("guard", "guard_admin")

@require_POST
def guard_call_resident(request, visitor_id):
    """
    Notify resident about pending visitor
    Creates notification for resident
    """
    try:
        visitor = Visitor.objects.select_related(
            "apartment"
        ).get(
            id=visitor_id,
            society=request.user.userprofile.society,
            status="pending"
        )
        
        # Get apartment residents
        residents = UserProfile.objects.filter(
            apartment=visitor.apartment,
            role="resident",
            status="approved"
        ).select_related("user")
        
        # Create notification for all residents in apartment
        for resident_profile in residents:
            resident_user = resident_profile.user

            # Ensure unique order
            user1, user2 = (
                (request.user, resident_user)
                if request.user.id < resident_user.id
                else (resident_user, request.user)
            )

            chatroom, created = ChatRoom.objects.get_or_create(
                user1=user1,
                user2=user2
            )

            ChatMessage.objects.create(
                chatroom=chatroom,
                sender=request.user,
                receiver=resident_user,
                message=f"🔔 {visitor.name} is waiting at the gate."
            )

            chatroom.updated_at = timezone.now()
            chatroom.save(update_fields=["updated_at"])


        
        messages.success(
            request,
            f"✓ Notification sent to residents of {visitor.apartment.block}-{visitor.apartment.flat_number}"
        )
        
        return JsonResponse({
            "success": True,
            "message": "Resident notified"
        })
        
    except Visitor.DoesNotExist:
        return JsonResponse({
            "success": False,
            "error": "Visitor not found"
        }, status=404)



@login_required
@role_required("admin")
def admin_dashboard(request):

    today = now().date()
    yesterday = today - timedelta(days=1)

    # ---------------- BASIC METRICS ----------------
    total_apartments = Apartment.objects.count()
    total_residents = UserProfile.objects.filter(role="resident").count()
    total_guards = UserProfile.objects.filter(role__in=["guard", "guard_admin"]).count()

    today_visitors = Visitor.objects.filter(created_at__date=today).count()
    yesterday_visitors = Visitor.objects.filter(created_at__date=yesterday).count()

    visitor_change = today_visitors - yesterday_visitors
    visitor_change_abs = abs(visitor_change)

    pending_deliveries = Delivery.objects.filter(
        status__iexact="pending"
    ).count()

    # ---------------- VISITORS ----------------
    pending_visitors = Visitor.objects.filter(
        status="pending"
    ).order_by("-created_at")

    recent_visitors = Visitor.objects.order_by(
        "-created_at"
    )[:6]

    # ---------------- COMPLAINTS ----------------
    complaints = Complaint.objects.select_related(
        "user", "apartment"
    ).order_by("-created_at")

    open_complaints_count = complaints.filter(
        status="open"
    ).count()

    # ---------------- ACTIVITY ----------------
    recent_announcements = Announcement.objects.order_by(
        "-created_at"
    )[:4]

    # ---------------- ANALYTICS ----------------
    visitor_stats = Visitor.objects.filter(
        created_at__date=today
    ).values(
        "visitor_type"
    ).annotate(
        count=Count("id")
    )

    # ---------------- RESIDENTS ----------------
    residents = UserProfile.objects.filter(
        role="resident"
    ).select_related(
        "apartment"
    )[:5]

    # ---------------- CONTEXT ----------------
    context = {
        "society_name": (
            Apartment.objects.first().society_name
            if Apartment.objects.exists() else "—"
        ),

        # Metrics
        "total_apartments": total_apartments,
        "total_residents": total_residents,
        "total_guards": total_guards,
        "today_visitors": today_visitors,
        "visitor_change": visitor_change,
        "visitor_change_abs": visitor_change_abs,
        "pending_deliveries": pending_deliveries,

        # Visitors
        "pending_visitors": pending_visitors,
        "pending_visitors_count": pending_visitors.count(),
        "recent_visitors": recent_visitors,

        # Complaints
        "complaints": complaints[:5],
        "open_complaints_count": open_complaints_count,

        # Activity
        "recent_announcements": recent_announcements,

        # Analytics
        "visitor_stats": visitor_stats,

        # Residents
        "residents": residents,
    }

    return render(request, "admin_index.html", context)

from django.db import transaction
@login_required
@role_required("admin")
def admin_residents(request):
    residents = UserProfile.objects.filter(
        role="resident"
    ).select_related("user", "apartment")

    return render(request, "admin_residents.html", {
        "residents": residents
    })

from django.db import transaction
from .models import Service

from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth import login
from core.models import UserProfile, ServiceProvider, Society, Apartment, Service

@transaction.atomic
def register_view(request):

    services = Service.objects.filter(active=True).order_by("name")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")
        role = request.POST.get("role")

        if not username or not password or not role:
            return render(request, "register.html", {
                "error": "All fields are required",
                "services": services
            })

        if User.objects.filter(username=username).exists():
            return render(request, "register.html", {
                "error": "Username already exists",
                "services": services
            })

        user = User.objects.create_user(username=username, password=password)

        # ✅ ALWAYS get_or_create
        profile, _ = UserProfile.objects.get_or_create(user=user)

        # ================= SERVICE PROVIDER =================
        if role == "service_provider":
            profile.role = "service_provider"
            profile.phone = request.POST.get("mobile")
            profile.status = "approved"
            profile.save()

            ServiceProvider.objects.create(
                user=user,
                service_id=request.POST.get("service"),
                name=request.POST.get("name"),
                mobile=request.POST.get("mobile"),
                alternate_mobile=request.POST.get("alternate_mobile", ""),
                gender=request.POST.get("gender"),
                age=request.POST.get("age") or None,
                area=request.POST.get("area"),
                city=request.POST.get("city"),
                pincode=request.POST.get("pincode"),
                experience_years=request.POST.get("experience_years", 0),
                hourly_rate=request.POST.get("hourly_rate") or None,
                monthly_rate=request.POST.get("monthly_rate") or None,
                preferred_timings=request.POST.get("preferred_timings"),
                available_days=request.POST.get("available_days"),
                police_verification=request.POST.get("police_verification") == "on",
                verification_status="verified"
            )

            login(request, user)
            return redirect("service_provider_dashboard")

        # ================= SOCIETY ADMIN =================
        if role == "society_admin":
            society = Society.objects.create(
                name=request.POST.get("society_name"),
                address=request.POST.get("address"),
                city=request.POST.get("city"),
                state=request.POST.get("state"),
                created_by=user
            )

            profile.role = "society_admin"
            profile.society = society
            profile.phone = request.POST.get("phone")
            profile.status = "approved"
            profile.save()

            login(request, user)
            return redirect("society_admin_dashboard")

        # ================= RESIDENT / GUARD =================
        society_code = request.POST.get("society_code", "").strip().upper()
        society = Society.objects.filter(society_code=society_code).first()

        if not society:
            raise transaction.TransactionManagementError("Invalid society code")

        profile.role = role
        profile.society = society
        profile.phone = request.POST.get("phone")
        profile.status = "pending"
        profile.save()

        if role == "resident":
            apartment, _ = Apartment.objects.get_or_create(
                society=society,
                block=request.POST.get("block"),
                flat_number=request.POST.get("flat_number")
            )
            profile.apartment = apartment
            profile.save()

        return render(request, "pending_approval.html")

    return render(request, "register.html", {
        "services": services
    })




@login_required
@role_required("society_admin")
def approve_user(request, id):
    profile = UserProfile.objects.get(
        id=id,
        society=request.user.userprofile.society
    )
    profile.status = "approved"
    profile.save()

    return redirect("society_admin_dashboard")


@login_required
@role_required("society_admin")
def society_admin_dashboard(request):
    profile = request.user.userprofile
    society = profile.society

    # ===== APARTMENTS =====
    total_apartments = society.apartments.count()

    # ===== MEMBERS =====
    pending_users = UserProfile.objects.filter(
        society=society,
        status="pending"
    ).select_related("user", "apartment")

    approved_residents = UserProfile.objects.filter(
        society=society,
        role="resident",
        status="approved"
    ).select_related("user", "apartment")

    approved_guards = UserProfile.objects.filter(
        society=society,
        role__in=["guard", "guard_admin"],
        status="approved"
    ).select_related("user")

    total_residents = approved_residents.count()
    total_guards = approved_guards.count()

    # ===== OCCUPANCY =====
    occupied_apartments = approved_residents.values("apartment").distinct().count()
    occupancy_pct = round((occupied_apartments / total_apartments * 100) if total_apartments > 0 else 0)

    # ===== NEW RESIDENTS (last 7 days) =====
    # UserProfile has no created_at; use User.date_joined instead
    week_ago = now() - timedelta(days=7)
    new_residents_week = UserProfile.objects.filter(
        society=society,
        role="resident",
        status="approved",
        user__date_joined__gte=week_ago
    ).count()

    # ===== VISITORS =====
    today = now().date()
    today_visitors_qs = Visitor.objects.filter(
        society=society,
        created_at__date=today
    )
    today_visitors_count = today_visitors_qs.count()

    yesterday_visitors_count = Visitor.objects.filter(
        society=society,
        created_at__date=today - timedelta(days=1)
    ).count()

    visitor_change = today_visitors_count - yesterday_visitors_count

    # ===== DELIVERIES =====
    # Delivery model has: apartment, company, tracking_id, otp, photo, status, received_at
    # No updated_at field — use received_at (set when delivered) for "delivered today"
    pending_deliveries_count = Delivery.objects.filter(
        apartment__society=society,
        status__iexact="pending"
    ).count()

    delivered_today = Delivery.objects.filter(
        apartment__society=society,
        status__iexact="delivered",
        received_at__date=today
    ).count()

    # ===== COMPLAINTS =====
    # Complaint model has: user, apartment, title, description, priority, status, created_at
    # No updated_at — use created_at as proxy for resolved_today
    all_complaints = Complaint.objects.filter(
        apartment__society=society
    ).order_by("-created_at")

    open_complaints_count = all_complaints.filter(status="open").count()

    resolved_today = Complaint.objects.filter(
        apartment__society=society,
        status="resolved",
        created_at__date=today
    ).count()

    # ===== ANNOUNCEMENTS =====
    recent_announcements = Announcement.objects.filter(
        society=society
    ).order_by("-created_at")[:5]

    # ===== ANALYTICS =====
    visitor_stats = today_visitors_qs.values("visitor_type").annotate(
        count=Count("id")
    ).order_by("-count")

    # ===== PENDING VISITORS =====
    pending_visitors_count = today_visitors_qs.filter(status="pending").count()

    context = {
        # Hero
        "society_name": society.name,
        "society_code": society.society_code,

        # Metrics
        "total_apartments": total_apartments,
        "total_residents": total_residents,
        "total_guards": total_guards,
        "today_visitors": today_visitors_count,
        "pending_deliveries": pending_deliveries_count,
        "open_complaints_count": open_complaints_count,

        # Real change indicators
        "occupancy_pct": occupancy_pct,
        "new_residents_week": new_residents_week,
        "visitor_change": visitor_change,
        "delivered_today": delivered_today,
        "resolved_today": resolved_today,

        # Approvals
        "pending_users": pending_users,

        # Lists
        "guards": approved_guards,
        "residents": approved_residents,
        "complaints": all_complaints[:5],
        "recent_announcements": recent_announcements,
        "recent_visitors": today_visitors_qs.order_by("-created_at")[:10],
        "visitor_stats": visitor_stats,

        # Counts
        "pending_visitors_count": pending_visitors_count,
    }

    return render(request, "society_admin/society_admin_dashboard.html", context)

@login_required
@role_required("society_admin")
def society_admin_residents(request):
    profile = request.user.userprofile
    society = profile.society

    if not society:
        return HttpResponse("Society not assigned to this admin", status=400)

    residents = (
        UserProfile.objects
        .filter(society=society, role="resident")
        .select_related("user", "apartment")
    )

    context = {
        "residents": residents,
        "total_apartments": society.apartments.count(),
        "active_count": residents.filter(status="approved").count(),
        "pending_count": residents.filter(status="pending").count(),
        "blocks": (
            society.apartments
            .values_list("block", flat=True)
            .distinct()
        ),
    }

    return render(
        request,
        "society_admin/society_admin_residents.html",
        context
    )
@login_required
@role_required("society_admin")
def society_admin_guards(request):
    profile = request.user.userprofile
    society = profile.society

    if not society:
        return HttpResponse("Society not assigned", status=400)

    guards = (
        UserProfile.objects
        .filter(society=society, role__in=["guard", "guard_admin"])
        .select_related("user")
    )

    context = {
        "guards": guards,
        "active_count": guards.filter(status="approved").count(),
        "pending_count": guards.filter(status="pending").count(),
    }

    return render(
        request,
        "society_admin/society_admin_guards.html",
        context
    )

@login_required
@role_required("society_admin")
def view_guard(request, id):
    guard = UserProfile.objects.select_related("user").get(id=id, role__in=["guard", "guard_admin"])
    return JsonResponse({
        "name": guard.user.get_full_name() or guard.user.username,
        "email": guard.user.email,
        "phone": guard.phone,
        "status": guard.status
    })


@login_required
@role_required("society_admin")
def edit_guard(request, id):
    guard = UserProfile.objects.select_related("user").get(id=id, role__in=["guard", "guard_admin"])
    return JsonResponse({
        "username": guard.user.username,
        "email": guard.user.email,
        "phone": guard.phone,
        "status": guard.status
    })


@login_required
@role_required("society_admin")
@require_POST
def update_guard(request):
    guard = UserProfile.objects.get(id=request.POST["guard_id"], role__in=["guard", "guard_admin"])
    user = guard.user

    user.username = request.POST["username"]
    user.email = request.POST.get("email", "")
    user.save()

    guard.phone = request.POST.get("phone")
    guard.status = request.POST.get("status")
    guard.save()

    return JsonResponse({"success": True})


@login_required
@role_required("society_admin")
@require_POST
def delete_guard(request):
    guard = UserProfile.objects.get(id=request.POST["guard_id"], role__in=["guard", "guard_admin"])
    guard.user.delete()
    return JsonResponse({"success": True})

@login_required
@role_required("society_admin")
def society_admin_view_resident(request, resident_id):
    profile = request.user.userprofile
    society = profile.society

    resident = get_object_or_404(
        UserProfile,
        id=resident_id,
        society=society,
        role="resident"
    )

    return JsonResponse({
        "success": True,
        "resident": {
            "name": resident.user.get_full_name() or resident.user.username,
            "email": resident.user.email,
            "phone": resident.phone,
            "apartment": (
                f"{resident.apartment.block} - {resident.apartment.flat_number}"
                if resident.apartment else None
            ),
            "block": resident.apartment.block if resident.apartment else None,
            "flat_number": resident.apartment.flat_number if resident.apartment else None,
            "status": resident.status,
            "joined_date": resident.user.date_joined.strftime("%d %b %Y"),
        }
    })

@login_required
@role_required("society_admin")
def society_admin_edit_resident(request, resident_id):
    profile = request.user.userprofile
    society = profile.society

    resident = get_object_or_404(
        UserProfile,
        id=resident_id,
        society=society,
        role="resident"
    )

    return JsonResponse({
        "success": True,
        "resident": {
            "username": resident.user.username,
            "email": resident.user.email,
            "phone": resident.phone,
            "block": resident.apartment.block if resident.apartment else "",
            "flat_number": resident.apartment.flat_number if resident.apartment else "",
            "status": resident.status,
        }
    })

@login_required
@role_required("society_admin")
@require_POST
def society_admin_update_resident(request):
    resident_id = request.POST.get("resident_id")

    resident = get_object_or_404(
        UserProfile,
        id=resident_id,
        society=request.user.userprofile.society,
        role="resident"
    )

    # Update User
    resident.user.username = request.POST.get("username")
    resident.user.email = request.POST.get("email")
    resident.user.save()

    # Update Profile
    resident.phone = request.POST.get("phone")
    resident.status = request.POST.get("status")

    # Update Apartment
    block = request.POST.get("block")
    flat_number = request.POST.get("flat_number")

    apartment, _ = Apartment.objects.get_or_create(
        society=resident.society,
        block=block,
        flat_number=flat_number
    )

    resident.apartment = apartment
    resident.save()

    return JsonResponse({
        "success": True,
        "message": "Resident updated successfully"
    })

@login_required
@role_required("society_admin")
@require_POST
def society_admin_delete_resident(request):
    resident_id = request.POST.get("resident_id")

    resident = get_object_or_404(
        UserProfile,
        id=resident_id,
        society=request.user.userprofile.society,
        role="resident"
    )

    # This deletes profile + user
    resident.user.delete()

    return JsonResponse({
        "success": True,
        "message": "Resident deleted successfully"
    })



@login_required
@role_required("society_admin")
def society_admin_analytics(request):
    profile = request.user.userprofile

    # ✅ SAFELY get society
    society = profile.society
    if not society:
        return HttpResponse("Society not assigned to this admin", status=400)

    visitor_stats = Visitor.objects.filter(
        society=society
    ).values(
        "visitor_type"
    ).annotate(
        count=Count("id")
    )

    context = {
        "today_visitors": Visitor.objects.filter(
            society=society,
            created_at__date=now().date()
        ).count(),

        "pending_deliveries": Delivery.objects.filter(
            apartment__society=society
        ).count(),

        "open_complaints_count": Complaint.objects.filter(
            apartment__society=society,
            status="open"
        ).count(),

        "recent_announcements": Announcement.objects.filter(
            society=society
        ),

        "visitor_stats": visitor_stats,

        "residents": UserProfile.objects.filter(
            society=society,
            role="resident"
        ),
    }

    return render(
        request,
        "society_admin/society_admin_analytics.html",
        context
    )



@login_required
@role_required("society_admin")
def society_admin_notices(request):
    """
    Society Admin Community Page:
    - Feed
    - Announcements
    - Polls
    """

    try:
        profile = request.user.userprofile
        society = profile.society

        if not society:
            messages.error(request, "You are not associated with any society.")
            return redirect("society_admin_dashboard")

        # ================= FEED =================
        posts = (
            CommunityPost.objects
            .filter(society=society)
            .select_related("user", "apartment")
            .order_by("-created_at")
        )

        # ================= ANNOUNCEMENTS =================
        announcements = (
            Announcement.objects
            .filter(society=society)
            .select_related("created_by")
            .order_by("-created_at")
        )

        # ================= POLLS =================
        polls = (
            Poll.objects
            .filter(society=society)
            .prefetch_related("options", "poll_votes")
            .order_by("-created_at")
        )

        # ================= ADMIN INTERACTIONS =================
        user_voted_polls = PollVote.objects.filter(
            user=request.user,
            poll__society=society
        ).values_list("poll_id", flat=True)

        liked_post_ids = PostLike.objects.filter(
            user=request.user,
            post__society=society
        ).values_list("post_id", flat=True)

        context = {
            "posts": posts,
            "announcements": announcements,
            "polls": polls,

            "user_voted_polls": list(user_voted_polls),
            "liked_post_ids": list(liked_post_ids),

            # 🔥 ADMIN FLAGS
            "is_admin": True,
            "user_role": "society_admin",
            "user_apartment": profile.apartment,
        }

        return render(
            request,
            "society_admin/society_admin_notices.html",
            context
        )

    except Exception as e:
        messages.error(request, f"Error loading community page: {str(e)}")
        return redirect("society_admin_dashboard")



@login_required
@role_required("society_admin")
def society_admin_create_announcement(request):
    profile = request.user.userprofile
    society = profile.society

    if request.method == "POST":
        Announcement.objects.create(
            society=society,
            title=request.POST.get("title"),
            message=request.POST.get("message"),
            category=request.POST.get("category"),
            created_by=request.user,
        )
        messages.success(request, "📢 Notice published successfully")

    return redirect("society_admin_notices")



@login_required
@role_required("society_admin")
def society_admin_settings(request):
    profile = request.user.userprofile
    society = profile.society

    if request.method == "POST":
        action = request.POST.get("action")

        # ─── UPDATE PROFILE & SOCIETY INFO ───────────────────────────────────
        if action == "update_profile":
            try:
                # Society fields
                society_name    = request.POST.get("society_name", "").strip()
                society_address = request.POST.get("society_address", "").strip()
                society_city    = request.POST.get("society_city", "").strip()
                society_state   = request.POST.get("society_state", "").strip()

                if society_name:    society.name    = society_name
                if society_address: society.address = society_address
                if society_city:    society.city    = society_city
                if society_state:   society.state   = society_state
                society.save()

                # Admin user fields
                username  = request.POST.get("username", "").strip()
                email     = request.POST.get("email", "").strip()
                phone     = request.POST.get("phone", "").strip()
                full_name = request.POST.get("full_name", "").strip()

                if username and username != request.user.username:
                    if User.objects.filter(username=username).exclude(id=request.user.id).exists():
                        return JsonResponse({"success": False, "error": "Username already taken"})
                    request.user.username = username

                if email:
                    request.user.email = email

                if full_name:
                    name_parts = full_name.split(" ", 1)
                    request.user.first_name = name_parts[0]
                    request.user.last_name  = name_parts[1] if len(name_parts) > 1 else ""

                request.user.save()

                if phone:
                    profile.phone = phone
                    profile.save()

                return JsonResponse({
                    "success": True,
                    "message": "Settings saved successfully!",
                    "updated_values": {
                        "society_name":    society.name,
                        "society_address": society.address,
                        "society_city":    society.city,
                        "society_state":   society.state,
                        "username":        request.user.username,
                        "email":           request.user.email,
                        "phone":           profile.phone,
                        "full_name": f"{request.user.first_name} {request.user.last_name}".strip(),
                    }
                })

            except Exception as e:
                return JsonResponse({"success": False, "error": f"Error saving settings: {str(e)}"})

        # ─── CHANGE PASSWORD ──────────────────────────────────────────────────
        elif action == "change_password":
            current  = request.POST.get("current_password", "")
            new_pw   = request.POST.get("new_password", "")
            confirm  = request.POST.get("confirm_password", "")

            if not request.user.check_password(current):
                return JsonResponse({"success": False, "error": "Current password is incorrect"})
            if len(new_pw) < 8:
                return JsonResponse({"success": False, "error": "New password must be at least 8 characters"})
            if new_pw != confirm:
                return JsonResponse({"success": False, "error": "Passwords do not match"})

            request.user.set_password(new_pw)
            request.user.save()
            # Re-authenticate so the session isn't invalidated
            update_session_auth_hash(request, request.user)
            return JsonResponse({"success": True, "message": "Password updated successfully!"})

        # ─── SECURITY SETTINGS ────────────────────────────────────────────────
        elif action == "update_security":
            # Expand this as you add security preference fields to your model
            return JsonResponse({"success": True, "message": "Security settings saved!"})

        # ─── NOTIFICATION PREFERENCES ─────────────────────────────────────────
        elif action == "update_notifications":
            # Expand this as you add notification preference fields to your model
            return JsonResponse({"success": True, "message": "Notification preferences saved!"})

    # ─── GET ─────────────────────────────────────────────────────────────────
    context = {
        "society": society,
        "user":    request.user,
    }
    return render(request, "society_admin/society_admin_settings.html", context)



def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@role_required("resident")
def send_sos(request):
    EmergencyAlert.objects.create(
        user=request.user,
        apartment=request.user.userprofile.apartment
    )

    guards = UserProfile.objects.filter(
        role__in=["guard", "guard_admin"],
        society=request.user.userprofile.society
    )
    for g in guards:
        Notification.objects.create(
            user=g.user,
            title="🚨 SOS Alert",
            message="Emergency reported by resident"
        )

    return JsonResponse({"status": "sent"})



@login_required
@role_required("resident")
def resident_directory(request):
    residents = UserProfile.objects.filter(
        society=request.user.userprofile.society,
        role="resident",
        status="approved"
    ).select_related("user", "apartment")

    return render(request, "resident_directory.html", {
        "residents": residents
    })



@login_required
@role_required("resident")
def resident_vehicles(request):
    profile = request.user.userprofile
    apartment = profile.apartment

    vehicles = Vehicle.objects.filter(apartment=apartment)

    context = {
        "vehicles": vehicles,
        "total_vehicles": vehicles.count(),
        "two_wheelers": vehicles.filter(vehicle_type="2wheeler").count(),
        "four_wheelers": vehicles.filter(vehicle_type="4wheeler").count(),
        "parking_slots": vehicles.exclude(parking_slot="").count(),
    }

    return render(request, "resident_vehicles.html", context)


@login_required
@require_POST
def add_vehicle(request):
    try:
        data = json.loads(request.body)

        profile = request.user.userprofile
        apartment = profile.apartment

        Vehicle.objects.create(
            apartment=apartment,
            vehicle_type=data.get("vehicle_type"),
            registration_number=data.get("registration_number").upper(),
            brand=data.get("brand", ""),
            model=data.get("model", ""),
            color=data.get("color", ""),
            parking_slot=data.get("parking_slot", ""),
            status="active"
        )

        return JsonResponse({
            "success": True
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)

@login_required
def get_vehicle(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        apartment=request.user.userprofile.apartment
    )

    return JsonResponse({
        "id": vehicle.id,
        "registration_number": vehicle.registration_number,  
        "vehicle_type": vehicle.vehicle_type,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "color": vehicle.color,
        "parking_slot": vehicle.parking_slot,
    })



@login_required
@require_POST
def update_vehicle(request, vehicle_id):
    data = json.loads(request.body)

    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        apartment=request.user.userprofile.apartment
    )

    vehicle.registration_number = data.get("registration_number").upper() 
    vehicle.vehicle_type = data.get("vehicle_type")
    vehicle.brand = data.get("brand")
    vehicle.model = data.get("model")
    vehicle.color = data.get("color")
    vehicle.parking_slot = data.get("parking_slot")
    vehicle.save()

    return JsonResponse({"success": True})

@login_required
def vehicle_history_api(request, vehicle_id):
    vehicle = get_object_or_404(
        Vehicle,
        id=vehicle_id,
        apartment=request.user.userprofile.apartment
    )

    # Example history (replace with DB table later if needed)
    history = [
        {
            "action": "Vehicle Added",
            "timestamp": vehicle.created_at.strftime("%d %b %Y, %I:%M %p")
        }
    ]

    if vehicle.updated_at:
        history.append({
            "action": "Vehicle Updated",
            "timestamp": vehicle.updated_at.strftime("%d %b %Y, %I:%M %p")
        })

    return JsonResponse({
        "history": history
    })


@login_required
@role_required("resident")
@require_http_methods(["DELETE"])
def delete_vehicle(request, vehicle_id):
    try:
        vehicle = Vehicle.objects.get(
            id=vehicle_id,
            apartment=request.user.userprofile.apartment
        )
        vehicle.delete()

        return JsonResponse({"success": True})

    except Vehicle.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Vehicle not found"
        }, status=404)

@login_required
def edit_vehicle(request, vehicle_id):
    # TEMP: redirect back until edit UI is implemented
    return redirect("resident_vehicles")


@login_required
def vehicle_history(request, vehicle_id):
    # TEMP: redirect back until history UI is implemented
    return redirect("resident_vehicles")

@login_required
@role_required("resident")
@require_POST
def verify_delivery_otp(request):
    otp = request.POST.get("otp")

    delivery = Delivery.objects.filter(
        apartment=request.user.userprofile.apartment,
        otp=otp,
        status__iexact="pending"
    ).first()

    if not delivery:
        return JsonResponse({"error": "Invalid OTP"}, status=400)

    delivery.status = "received"
    delivery.received_at = now()
    delivery.save()

    Notification.objects.create(
        user=request.user,
        title="Parcel Received",
        message=f"Parcel from {delivery.company} received"
    )

    return JsonResponse({"success": True})


@login_required
@role_required("service_provider")
def service_provider_dashboard(request):
    """
    Service Provider Dashboard - Overview of stats and recent activity
    """
    provider = request.user.service_provider_profile

    active_clients = HiredService.objects.filter(
        service_provider=provider,
        status="active"
    ).select_related("resident", "resident__userprofile")

    context = {
        "provider": provider,
        "active_clients": active_clients,
        "total_clients": provider.total_hires,
        "rating": provider.rating,
        "reviews": provider.total_reviews,
    }

    return render(request, "service_provider/service_provider_dashboard.html", context)

def update_provider_rating(provider):
    qs = ServiceReview.objects.filter(
        hired_service__service_provider=provider
    )

    stats = qs.aggregate(
        avg_rating=Avg("rating"),
        total=Count("id")
    )

    provider.rating = round(stats["avg_rating"] or 0, 1)
    provider.total_reviews = stats["total"]
    provider.save(update_fields=["rating", "total_reviews"])


@login_required
@role_required("resident")
def add_service_review(request, hired_id):
    if request.method != "POST":
        return redirect("resident_services")

    hired_service = get_object_or_404(
        HiredService,
        id=hired_id,
        resident=request.user
    )

    # 🔒 Prevent duplicate review
    if ServiceReview.objects.filter(hired_service=hired_service).exists():
        return redirect(
            "service_provider_detail",
            provider_id=hired_service.service_provider.id
        )

    rating = int(request.POST.get("rating", 0))
    review_text = request.POST.get("review_text", "").strip()

    # ❌ SAFETY CHECK
    if rating < 1 or rating > 5 or not review_text:
        return redirect(
            "service_provider_detail",
            provider_id=hired_service.service_provider.id
        )

    # ✅ SAVE REVIEW
    ServiceReview.objects.create(
        hired_service=hired_service,
        rating=rating,
        review_text=review_text
    )

    # ✅ UPDATE PROVIDER RATING
    provider = hired_service.service_provider
    all_reviews = ServiceReview.objects.filter(
        hired_service__service_provider=provider
    )

    provider.total_reviews = all_reviews.count()
    provider.rating = round(
        sum(r.rating for r in all_reviews) / provider.total_reviews,
        1
    )
    provider.save(update_fields=["rating", "total_reviews"])

    return redirect(
        "service_provider_detail",
        provider_id=provider.id
    )



@login_required
@role_required("service_provider")
def service_provider_clients(request):
    """
    View all clients (active, paused, terminated)
    """
    provider = request.user.service_provider_profile

    all_clients = HiredService.objects.filter(
        service_provider=provider
    ).select_related(
        "resident",
        "resident__userprofile",
        "resident__userprofile__apartment",
        "resident__userprofile__apartment__society"
    ).order_by("-created_at")

    active_clients = all_clients.filter(status="active")
    paused_clients = all_clients.filter(status="paused")
    terminated_clients = all_clients.filter(status="terminated")

    context = {
        "provider": provider,
        "all_clients": all_clients,
        "active_clients": active_clients,
        "paused_clients": paused_clients,
        "terminated_clients": terminated_clients,
    }

    return render(request, "service_provider/service_provider_clients.html", context)


@login_required
@role_required("service_provider")
def service_provider_client_detail(request, hired_id):
    """
    Detailed view of a specific client relationship
    """
    provider = request.user.service_provider_profile
    
    hired = get_object_or_404(
        HiredService.objects.select_related(
            "resident",
            "resident__userprofile",
            "resident__userprofile__apartment",
            "resident__userprofile__apartment__society"
        ),
        id=hired_id,
        service_provider=provider
    )
    
    context = {
        "provider": provider,
        "hired": hired,
    }
    
    return render(request, "service_provider/service_provider_client_detail.html", context)


@login_required
@role_required("service_provider")
def service_provider_requests(request):
    """
    View and manage hire requests from residents
    Note: This requires a HireRequest model or using HiredService with a 'pending' status
    """
    provider = request.user.service_provider_profile

    # If you have a separate HireRequest model, use it
    # Otherwise, you can use HiredService with status filters
    # For now, showing example with HiredService assuming you might add more statuses
    
    # Pending requests (you may need to add 'pending' status to HiredService)
    pending_requests = HiredService.objects.filter(
        service_provider=provider,
        status="pending"  # You'll need to add this status option
    ).select_related(
        "resident",
        "resident__userprofile",
        "resident__userprofile__apartment"
    ).order_by("-created_at")

    accepted_requests = HiredService.objects.filter(
        service_provider=provider,
        status="active"
    ).select_related(
        "resident",
        "resident__userprofile"
    ).order_by("-created_at")

    # For declined, you may need to track this separately or add a 'declined' status
    declined_requests = []

    context = {
        "provider": provider,
        "pending_requests": pending_requests,
        "accepted_requests": accepted_requests,
        "declined_requests": declined_requests,
    }

    return render(request, "service_provider/service_provider_requests.html", context)


@login_required
@role_required("service_provider")
@require_POST
def accept_hire_request(request, hired_id):
    """
    Accept a hire request from a resident
    """
    provider = request.user.service_provider_profile
    
    try:
        hired = HiredService.objects.get(
            id=hired_id,
            service_provider=provider,
            status="pending"
        )
        
        hired.status = "active"
        hired.save()
                
        resident = hired.resident

        user1, user2 = (
            (request.user, resident)
            if request.user.id < resident.id
            else (resident, request.user)
        )

        chatroom, created = ChatRoom.objects.get_or_create(
            user1=user1,
            user2=user2
        )

        ChatMessage.objects.create(
            chatroom=chatroom,
            sender=request.user,
            receiver=resident,
            message="✅ Your hire request has been accepted. We can coordinate here."
        )

        # Update provider stats
        provider.active_clients += 1
        provider.save()
        
        messages.success(
            request,
            f"✅ You have accepted the hire request from {hired.resident.first_name}"
        )
        
    except HiredService.DoesNotExist:
        messages.error(request, "Hire request not found")
    
    return redirect("service_provider_requests")


@login_required
@role_required("service_provider")
@require_POST
def decline_hire_request(request, hired_id):
    """
    Decline a hire request from a resident
    """
    provider = request.user.service_provider_profile
    
    try:
        hired = HiredService.objects.get(
            id=hired_id,
            service_provider=provider,
            status="pending"
        )
        
        # Either delete or mark as declined
        hired.status = "terminated"
        hired.save()

        
        messages.info(
            request,
            f"You have declined the hire request from {hired.resident.first_name}"
        )
        
    except HiredService.DoesNotExist:
        messages.error(request, "Hire request not found")
    
    return redirect("service_provider_requests")


@login_required
@role_required("service_provider")
def service_provider_profile(request):
    """
    View & edit service provider profile.
    Editing affects ONLY future hires.
    """
    provider = request.user.service_provider_profile

    if request.method == "POST":
        provider.name = request.POST.get("name")
        provider.mobile = request.POST.get("mobile")
        provider.alternate_mobile = request.POST.get("alternate_mobile", "")
        provider.gender = request.POST.get("gender")
        provider.age = request.POST.get("age") or None
        provider.area = request.POST.get("area")
        provider.city = request.POST.get("city")
        provider.pincode = request.POST.get("pincode")
        provider.full_address = request.POST.get("full_address", "")
        provider.experience_years = int(request.POST.get("experience_years", 0))
        provider.hourly_rate = request.POST.get("hourly_rate") or None
        provider.monthly_rate = request.POST.get("monthly_rate") or None
        provider.available_days = request.POST.get("available_days")
        provider.preferred_timings = request.POST.get("preferred_timings")
        provider.is_available = request.POST.get("is_available") == "on"

        provider.save()

        messages.success(
            request,
            "✅ Profile updated successfully. Existing hired residents will continue seeing previous details."
        )

        return redirect("service_provider_profile")

    return render(
        request,
        "service_provider/service_provider_profile.html",
        {"provider": provider}
    )

















# Add these views to your views.py file

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.db.models import Q, Max, Count, Case, When, IntegerField
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Import the chat models (adjust import path as needed)
from .models import ChatRoom, ChatMessage, UserOnlineStatus, UserProfile, Society


@login_required
@require_http_methods(["GET"])
def get_chats(request):
    """
    Get all chat conversations for the current user
    Returns list with last message, unread count, and message status
    """
    user = request.user
    
    # Get all chatrooms where user is a participant
    chatrooms = ChatRoom.objects.filter(
        Q(user1=user) | Q(user2=user)
    ).select_related('user1', 'user2').prefetch_related('messages')
    
    chats_data = []
    
    for chatroom in chatrooms:
        other_user = chatroom.get_other_user(user)
        last_message_obj = chatroom.get_last_message()
        if not last_message_obj:
            continue  # Skip empty chats
        
        # Get user's profile for role info
        try:
            other_profile = other_user.userprofile
            user_role = other_profile.get_role_display()
        except:
            user_role = "Member"
        
        # Determine message status
        is_sent_by_me = last_message_obj.sender == user
        is_delivered = last_message_obj.status == 'delivered'
        is_read = last_message_obj.is_read
        
        # Format time
        created = last_message_obj.created_at

        # Convert to local time safely
        if timezone.is_naive(created):
            created = timezone.make_aware(created, timezone.get_current_timezone())

        local_time = timezone.localtime(created)
        now = timezone.localtime(timezone.now())

        time_diff = now.date() - local_time.date()

        if time_diff.days == 0:
            time_str = local_time.strftime("%I:%M %p")
        elif time_diff.days == 1:
            time_str = "Yesterday"
        elif time_diff.days < 7:
            time_str = local_time.strftime("%A")
        else:
            time_str = local_time.strftime("%d/%m/%y")
        
        chat_data = {
            'chat_id': chatroom.id,
            'user_id': other_user.id,
            'user_name': other_user.get_full_name() or other_user.username,
            'user_role': user_role,
            'last_message': last_message_obj.message[:50] + ('...' if len(last_message_obj.message) > 50 else ''),
            'time': time_str,
            'timestamp': local_time.isoformat(), 
            'unread_count': chatroom.get_unread_count(user),
            'is_sent_by_me': is_sent_by_me,
            'is_delivered': is_delivered,
            'is_read': is_read,
        }
        
        chats_data.append(chat_data)
    
    # Sort by most recent activity
    chats_data.sort(key=lambda x: chatrooms.get(id=x['chat_id']).updated_at, reverse=True)
    
    return JsonResponse({
        'success': True,
        'chats': chats_data
    })


@login_required
@require_http_methods(["GET"])
def get_chat_messages(request, chat_id):
    """
    Get all messages for a specific chat
    """
    user = request.user
    
    chatroom = get_object_or_404(
        ChatRoom,
        Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
    )


    
    messages = chatroom.messages.select_related('sender', 'receiver').all()
    
    messages_data = []
    current_date = None
    
    for msg in messages:
        msg_date = msg.created_at.date()
        
        # Format date for divider
        if msg_date != current_date:
            current_date = msg_date
            today = timezone.now().date()
            yesterday = today - timedelta(days=1)
            
            if msg_date == today:
                date_str = "Today"
            elif msg_date == yesterday:
                date_str = "Yesterday"
            else:
                date_str = msg_date.strftime("%d %B %Y")
        else:
            date_str = None
        
        # Message data
        is_sent_by_me = msg.sender == user
        
        message_data = {
            'id': msg.id,
            'text': msg.message,
            'time': timezone.localtime(msg.created_at).strftime("%I:%M %p"),
            'timestamp': timezone.localtime(msg.created_at).isoformat(), 
            'date': date_str,
            'is_sent_by_me': is_sent_by_me,
            'is_delivered': msg.status == 'delivered',
            'is_read': msg.is_read,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
        }
        
        # Auto-mark received messages as delivered
        if not is_sent_by_me and msg.status == 'sent':
            msg.mark_as_delivered()
            message_data['is_delivered'] = True
        
        messages_data.append(message_data)
    
    return JsonResponse({
        'success': True,
        'messages': messages_data
    })


@login_required
@require_POST
def send_message(request, chat_id):
    """
    Send a new message in a chat
    """
    user = request.user
    
    chatroom = get_object_or_404(
        ChatRoom,
        Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
    )


    
    try:
        data = json.loads(request.body)
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return JsonResponse({
                'success': False,
                'error': 'Message cannot be empty'
            }, status=400)
        
        # Get receiver
        receiver = chatroom.get_other_user(user)
        
        # Create message
        message = ChatMessage.objects.create(
            chatroom=chatroom,
            sender=user,
            receiver=receiver,
            message=message_text,
            status='sent'
        )
        # Simulate delivery after 2 seconds logic (optional)
        message.status = "delivered"
        message.save(update_fields=["status"])

        # Update chatroom timestamp
        chatroom.updated_at = timezone.now()
        chatroom.save(update_fields=['updated_at'])
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'time': message.created_at.strftime("%I:%M %p")
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)


@login_required
@require_POST
def mark_chat_as_read(request, chat_id):
    """
    Mark all messages in a chat as read (WhatsApp blue double tick)
    """
    user = request.user
    
    chatroom = get_object_or_404(
        ChatRoom,
        Q(id=chat_id) & (Q(user1=user) | Q(user2=user))
    )


    
    # Mark all unread messages sent TO this user as read
    unread_messages = chatroom.messages.filter(
        receiver=user,
        is_read=False
    )
    
    for msg in unread_messages:
        msg.mark_as_read()
    
    return JsonResponse({
        'success': True,
        'marked_count': unread_messages.count()
    })

@login_required
@require_http_methods(["GET"])
def get_society_members(request):
    user = request.user

    try:
        profile = user.userprofile

        # 🔥 SERVICE PROVIDER CASE
        if profile.role == "service_provider":
            provider = user.service_provider_profile

            hired_clients = HiredService.objects.filter(
                service_provider=provider,
                status__in=["active", "paused"]
            ).select_related(
                "resident",
                "resident__userprofile",
                "resident__userprofile__apartment"
            )

            members_data = []

            for hire in hired_clients:
                resident = hire.resident
                profile = resident.userprofile

                members_data.append({
                    "id": resident.id,
                    "name": resident.get_full_name() or resident.username,
                    "role": "Client",
                    "apartment": (
                        f"{profile.apartment.block}-{profile.apartment.flat_number}"
                        if profile.apartment else "N/A"
                    ),
                })

            return JsonResponse({
                "success": True,
                "members": members_data
            })

        # 🔥 NORMAL USERS
        society = profile.society

        members = UserProfile.objects.filter(
            society=society,
            status="approved"
        ).exclude(user=user).select_related("user")

        members_data = [
            {
                "id": m.user.id,
                "name": m.user.get_full_name() or m.user.username,
                "role": m.get_role_display(),
                "apartment": (
                    f"{m.apartment.block}-{m.apartment.flat_number}"
                    if m.apartment else "N/A"
                )
            }
            for m in members
        ]

        return JsonResponse({
            "success": True,
            "members": members_data
        })

    except:
        return JsonResponse({
            "success": False,
            "error": "Something went wrong"
        }, status=400)



@login_required
@require_POST
def create_or_get_chat(request):
    """
    Create a new chat or get existing chat with another user
    """
    user = request.user
    
    try:
        data = json.loads(request.body)
        other_user_id = data.get('user_id')
        
        if not other_user_id:
            return JsonResponse({
                'success': False,
                'error': 'User ID required'
            }, status=400)
        
        other_user = get_object_or_404(User, id=other_user_id)
        
        # Check if users are in the same society
        try:
            user_society = user.userprofile.society
            other_society = other_user.userprofile.society
            
            if user_society != other_society:
                return JsonResponse({
                    'success': False,
                    'error': 'Can only chat with members of your society'
                }, status=403)
        except:
            pass
        
        # Get or create chatroom (order users by ID to ensure uniqueness)
        user1, user2 = (user, other_user) if user.id < other_user.id else (other_user, user)
        
        chatroom, created = ChatRoom.objects.get_or_create(
            user1=user1,
            user2=user2
        )
        
        return JsonResponse({
            'success': True,
            'chat_id': chatroom.id,
            'created': created
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)


@login_required
@require_http_methods(["GET"])
def get_user_status(request, user_id):
    """
    Get online status of a user
    """
    user = get_object_or_404(User, id=user_id)
    
    try:
        status = user.online_status
        
        if status.is_online:
            return JsonResponse({
                'success': True,
                'is_online': True,
                'last_seen': None
            })
        else:
            # Format last seen
            time_diff = timezone.now() - status.last_seen
            
            if time_diff.total_seconds() < 60:
                last_seen_str = "just now"
            elif time_diff.total_seconds() < 3600:
                minutes = int(time_diff.total_seconds() / 60)
                last_seen_str = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            elif time_diff.total_seconds() < 86400:
                hours = int(time_diff.total_seconds() / 3600)
                last_seen_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.days == 1:
                last_seen_str = "yesterday"
            else:
                last_seen_str = status.last_seen.strftime("%d/%m/%y")
            
            return JsonResponse({
                'success': True,
                'is_online': False,
                'last_seen': last_seen_str
            })
    except UserOnlineStatus.DoesNotExist:
        # Create status if doesn't exist
        UserOnlineStatus.objects.create(user=user, is_online=False)
        return JsonResponse({
            'success': True,
            'is_online': False,
            'last_seen': 'recently'
        })


@login_required
@require_POST
def update_online_status(request):
    """
    Update user's online status (called periodically from frontend)
    """
    user = request.user
    
    status, created = UserOnlineStatus.objects.get_or_create(user=user)
    status.is_online = True
    status.last_seen = timezone.now()
    status.save()
    
    return JsonResponse({'success': True})


@login_required
@require_POST
def set_offline_status(request):
    """
    Set user as offline (called on page unload)
    """
    user = request.user
    
    try:
        status = user.online_status
        status.is_online = False
        status.last_seen = timezone.now()
        status.save()
    except UserOnlineStatus.DoesNotExist:
        UserOnlineStatus.objects.create(user=user, is_online=False)
    
    return JsonResponse({'success': True})


# ========== UTILITY FUNCTION ==========

def auto_mark_messages_delivered():
    """
    Background task to auto-mark sent messages as delivered
    Can be called from a management command or celery task
    """
    # Mark all 'sent' messages older than 5 seconds as 'delivered'
    cutoff_time = timezone.now() - timedelta(seconds=5)
    
    messages = ChatMessage.objects.filter(
        status='sent',
        created_at__lt=cutoff_time
    )
    
    for msg in messages:
        msg.mark_as_delivered()
    
    return messages.count()


@login_required
@role_required("service_provider")
def service_provider_notifications(request):
    """
    Service Provider Messages/Notifications Page
    WhatsApp-like chat interface for service providers
    Allows them to communicate with:
    - Residents (current and potential clients)
    - Society admins
    - Guards (for entry notifications)
    """
    user = request.user
    
    try:
        provider = user.service_provider_profile
        
        context = {
            'provider': provider,
            'user': user,
        }
        
        return render(request, 'service_provider/service_provider_notifications.html', context)
    
    except Exception as e:
        # If service provider profile doesn't exist, redirect to dashboard
        from django.contrib import messages
        messages.error(request, "Service provider profile not found")
        return redirect('service_provider_dashboard')

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Bill, BillPayer, Notification, UserProfile


# ─────────────────────────────────────────
# POST /api/bills/create/
# ─────────────────────────────────────────
@login_required
@require_POST
def api_create_bill(request):
    try:
        profile = request.user.userprofile
        society = profile.society

        if profile.role != 'society_admin':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        data = json.loads(request.body)

        title       = data.get('title', '').strip()
        category    = data.get('category', '').strip()
        amount      = data.get('amount')
        due_date    = data.get('due_date')
        description = data.get('description', '').strip()
        payer_ids   = data.get('payer_ids', [])

        # Basic validation
        if not all([title, category, amount, due_date]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'})
        if not payer_ids:
            return JsonResponse({'success': False, 'error': 'Select at least one payer'})

        # Validate payers belong to the same society
        valid_users = User.objects.filter(
            id__in=payer_ids,
            userprofile__society=society,
            userprofile__status='approved'
        )

        bill = Bill.objects.create(
            society=society,
            created_by=request.user,
            title=title,
            category=category,
            amount=amount,
            due_date=due_date,
            description=description,
        )

        # Create BillPayer rows
        bill_payers = [
            BillPayer(bill=bill, user=u)
            for u in valid_users
        ]
        BillPayer.objects.bulk_create(bill_payers)

        # Send notifications to all payers
        notifications = [
            Notification(
                user=u,
                sender=request.user,
                title=f"💳 New Bill: {title}",
                message=(
                    f"₹{amount} due by {due_date}."
                    + (f" {description}" if description else '')
                )
            )
            for u in valid_users
        ]
        Notification.objects.bulk_create(notifications)

        return JsonResponse({
            'success': True,
            'message': f'Bill created for {len(bill_payers)} payer(s)!',
            'bill_id': bill.id,
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ─────────────────────────────────────────
# GET /api/bills/<bill_id>/
# ─────────────────────────────────────────
@login_required
def api_bill_detail(request, bill_id):
    try:
        profile = request.user.userprofile
        bill = Bill.objects.prefetch_related(
            'billpayer_set__user__userprofile'
        ).get(id=bill_id, society=profile.society)

        payers_data = []
        for bp in bill.billpayer_set.all():
            up = getattr(bp.user, 'userprofile', None)
            apt = ''
            if up and up.apartment:
                apt = f"{up.apartment.block}-{up.apartment.flat_number}"
            payers_data.append({
                'name': bp.user.get_full_name() or bp.user.username,
                'apartment': apt,
                'status': bp.status,
                'paid_at': bp.paid_at.strftime('%d %b %Y') if bp.paid_at else None,
            })

        paid_count    = sum(1 for p in payers_data if p['status'] == 'paid')
        pending_count = sum(1 for p in payers_data if p['status'] != 'paid')

        return JsonResponse({
            'success': True,
            'bill': {
                'id':            bill.id,
                'title':         bill.title,
                'category':      bill.get_category_display(),
                'amount':        str(bill.amount),
                'due_date':      bill.due_date.strftime('%d %b %Y'),
                'description':   bill.description,
                'status':        bill.status,
                'paid_count':    paid_count,
                'pending_count': pending_count,
                'payers':        payers_data,
            }
        })

    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ─────────────────────────────────────────
# POST /api/bills/<bill_id>/remind/
# ─────────────────────────────────────────
@login_required
@require_POST
def api_bill_remind(request, bill_id):
    try:
        profile = request.user.userprofile
        bill = Bill.objects.get(id=bill_id, society=profile.society)

        if profile.role != 'society_admin':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        # Find pending payers
        pending_payers = bill.billpayer_set.filter(status='pending').select_related('user')

        if not pending_payers.exists():
            return JsonResponse({'success': True, 'message': 'No pending payers to remind!'})

        notifications = [
            Notification(
                user=bp.user,
                sender=request.user,
                title=f"⏰ Payment Reminder: {bill.title}",
                message=f"₹{bill.amount} is due by {bill.due_date.strftime('%d %b %Y')}. Please pay at the earliest."
            )
            for bp in pending_payers
        ]
        Notification.objects.bulk_create(notifications)

        return JsonResponse({
            'success': True,
            'message': f'Reminder sent to {len(notifications)} payer(s)!'
        })

    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ─────────────────────────────────────────
# POST /api/bills/<bill_id>/delete/
# ─────────────────────────────────────────
@login_required
@require_POST
def api_bill_delete(request, bill_id):
    try:
        profile = request.user.userprofile

        if profile.role != 'society_admin':
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        bill = Bill.objects.get(id=bill_id, society=profile.society)
        bill.delete()

        return JsonResponse({'success': True, 'message': 'Bill deleted successfully'})

    except Bill.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Bill not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# ─────────────────────────────────────────
# Updated society_admin_notifications view
# ─────────────────────────────────────────
@login_required
def society_admin_notifications(request):
    """
    Society Admin Notifications Page
    Tabs: Alerts | Payments (bills/fines) | Messages
    """
    from django.contrib import messages as django_messages
    from .models import ChatMessage, Notification

    user = request.user
    try:
        profile = user.userprofile
        society = profile.society

        if not society:
            django_messages.error(request, "You are not associated with any society")
            return redirect('society_admin_dashboard')

        # ── Notifications / Alerts ──────────────────────────────
        notifications = Notification.objects.filter(
            user=user
        ).order_by('-created_at')

        unread_count = notifications.filter(is_read=False).count()
        notifications.filter(is_read=False).update(is_read=True)

        # ── Bills / Payments ────────────────────────────────────
        # Auto-mark overdue bills before fetching
        today = timezone.now().date()
        Bill.objects.filter(
            society=society,
            status='pending',
            due_date__lt=today
        ).update(status='overdue')

        bills = Bill.objects.filter(
            society=society
        ).prefetch_related('billpayer_set').order_by('-created_at')

        # Annotate each bill with aggregated payer counts
        bills_annotated = []
        for bill in bills:
            payers     = bill.billpayer_set.all()
            total      = payers.count()
            paid_c     = payers.filter(status='paid').count()
            paid_pct   = round((paid_c / total * 100) if total else 0)
            bill.total_payers = total
            bill.paid_count   = paid_c
            bill.paid_pct     = paid_pct
            bills_annotated.append(bill)

        pending_bills_count = sum(1 for b in bills_annotated if b.status == 'pending')
        paid_bills_count    = sum(1 for b in bills_annotated if b.status == 'paid')
        total_overdue       = sum(1 for b in bills_annotated if b.status == 'overdue')

        # ── Total unread chat messages ──────────────────────────
        total_unread = ChatMessage.objects.filter(
            receiver=user,
            is_read=False
        ).count()

        context = {
            'profile':             profile,
            'society':             society,
            'user':                user,
            # Alerts
            'notifications':       notifications,
            'unread_count':        unread_count,
            # Payments
            'bills':               bills_annotated,
            'pending_bills_count': pending_bills_count,
            'paid_bills_count':    paid_bills_count,
            'total_overdue':       total_overdue,
            # Chat
            'total_unread':        total_unread,
        }
        return render(request, 'society_admin/society_admin_notifications.html', context)

    except Exception as e:
        from django.contrib import messages as django_messages
        django_messages.error(request, f"Error loading notifications: {str(e)}")
        return redirect('society_admin_dashboard')


@login_required
def unread_count_api(request):
    """
    Returns total unread count for the logged-in user.
    Used by the base template's live badge polling script.
    """
    try:
        unread_chat = ChatMessage.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()

        unread_notif = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        total = unread_chat + unread_notif

    except Exception:
        total = 0

    return JsonResponse({'count': total})