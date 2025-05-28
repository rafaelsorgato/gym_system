import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class LoginForm(forms.Form):
    username = forms.CharField(
        label=False,
        max_length=150,
        required=True,
        widget=forms.TextInput(
            attrs={"placeholder": "Username", "class": "form-control"}
        ),
    )
    password = forms.CharField(
        label=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Password", "class": "form-control"}
        ),
    )


class ProfileForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        label="Password",
        help_text="Leave blank if you don't want to change it.",
    )
    profile_pic = forms.ImageField(required=False, label="Profile Picture")

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "id": "first_name"}),
        label="Name",
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "id": "email"}),
        label="Email",
    )

    class Meta:
        model = User
        fields = ["first_name", "email", "phone", "profile_picture"]

        widgets = {
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "id": "first_name"}
            ),
            "email": forms.EmailInput(attrs={"class": "form-control", "id": "email"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "id": "phone"}),
        }

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if password:
            if len(password) < 10 or not re.search(r"[!@#$%&*]", password):
                raise ValidationError(
                    "Password must be at least 10 characters long and contain special characters [!@#$%&*]."
                )
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)

        profile_pic = self.cleaned_data.get("profile_pic")
        if profile_pic:
            user.profile_picture = profile_pic

        if commit:
            user.save()
        return user
