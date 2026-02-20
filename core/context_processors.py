from core.models import Notification

def base_context(request):
    if not request.user.is_authenticated:
        return {}

    profile = getattr(request.user, "userprofile", None)

    return {
        "current_user": request.user,
        "current_role": profile.role if profile else None,
        "notification_count": Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count(),
    }



from .models import Notification, ChatMessage

def global_context(request):
    if not request.user.is_authenticated:
        return {
            "notification_count": 0,
            "current_user": None,
            "current_role": None,
        }

    user = request.user
    profile = getattr(user, "userprofile", None)

    # Count unread chat messages
    unread_chat = ChatMessage.objects.filter(
        receiver=user,
        is_read=False
    ).count()

    # Count unread system notifications
    unread_notifications = Notification.objects.filter(
        user=user,
        is_read=False
    ).count()

    return {
        "current_user": user,
        "current_role": profile.role if profile else None,
        "notification_count": unread_chat + unread_notifications,
    }



from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        return {
            "notification_count": Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        }
    return {"notification_count": 0}

def guard_notification_count(request):
    if (
        request.user.is_authenticated
        and hasattr(request.user, "userprofile")
        and request.user.userprofile.role == "guard"
    ):
        return {
            "guard_notification_count": Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
        }

    return {"guard_notification_count": 0}


# core/context_processors.py
# Add 'core.context_processors.notification_count' to
# TEMPLATES[0]['OPTIONS']['context_processors'] in settings.py

from .models import ChatMessage, Notification


def notification_count(request):
    """
    Injects `notification_count` (total unread messages + unread app
    notifications) into every template rendered via RequestContext.
    Safe — returns 0 for anonymous or unauthenticated users.
    """
    if not request.user.is_authenticated:
        return {'notification_count': 0}

    try:
        # Unread chat messages sent TO this user
        unread_chat = ChatMessage.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()

        # Unread in-app notifications (Notification model)
        unread_notif = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        total = unread_chat + unread_notif

    except Exception:
        total = 0

    return {'notification_count': total}