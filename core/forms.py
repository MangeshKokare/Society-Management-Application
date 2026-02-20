from django import forms
from django.contrib.auth.models import User
from .models import UserProfile

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["phone", "address"]
        widgets = {
            "address": forms.Textarea(attrs={
                "rows": 2,
                "readonly": "readonly",
                "style": "resize:none;"
            })
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

