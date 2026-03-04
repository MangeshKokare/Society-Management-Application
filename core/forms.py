from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

# forms.py  ·  Profile-related forms
# Add these to your existing forms.py

from django import forms
from django.contrib.auth.models import User
from .models import UserProfile


class UserEmailForm(forms.ModelForm):
    """Update User.email"""
    class Meta:
        model  = User
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class':       'form-control',
                'placeholder': 'your@email.com',
            })
        }


class ProfileEditForm(forms.ModelForm):
    """
    Update UserProfile fields.

    NOTE: photo, cover_photo, work, hometown, interests are handled
    separately in the view (form_type routing). This form covers the
    core fields that are always present on UserProfile.

    If your UserProfile does not yet have work / hometown / interests
    fields, add them as TextField(blank=True) in models.py and run
    makemigrations before using this form.
    """

    class Meta:
        model  = UserProfile
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': '+91 XXXXX XXXXX',
            }),
            'address': forms.TextInput(attrs={
                'class':       'form-control',
                'placeholder': 'Your address',
            }),
        }




class UserEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]

        widgets = {
            "email": forms.EmailInput(attrs={
                "class": "form-input",
                "placeholder": "Enter email",
                "readonly": "readonly"
            })
        }


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "address"]

