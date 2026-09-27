from django import forms

from .models import EcocashPayment


class EcocashPaymentForm(forms.ModelForm):
    class Meta:
        model = EcocashPayment
        fields = ["sender_phone_number"]
        widgets = {
            "sender_phone_number": forms.TextInput(
                attrs={"placeholder": "07XXXXXXXX — the number you paid from"}
            )
        }
