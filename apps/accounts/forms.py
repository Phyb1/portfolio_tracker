from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        required=False, help_text="Optional. Used for EcoCash payment matching."
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit and self.cleaned_data.get("phone_number"):
            user.profile.phone_number = self.cleaned_data["phone_number"]
            user.profile.save(update_fields=["phone_number"])
        return user
