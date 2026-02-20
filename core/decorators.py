from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden
from core.models import UserProfile


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("login")

            profile = get_object_or_404(UserProfile, user=request.user)

            if profile.role not in roles:
                return HttpResponseForbidden(
                    "You are authenticated, but not authorized to access this page."
                )

            if profile.status != "approved":
                return redirect("pending_approval")

            return view_func(request, *args, **kwargs)

        return wrapper
    return decorator
