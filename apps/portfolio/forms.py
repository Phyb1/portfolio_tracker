from django import forms

from apps.markets.models import Counter


class AddHoldingForm(forms.Form):
    """Enter counter name + quantity — the core input described in the brief."""

    counter = forms.ModelChoiceField(
        queryset=Counter.objects.filter(status=Counter.STATUS_ACTIVE).select_related("exchange"),
        label="Counter",
    )
    quantity = forms.IntegerField(min_value=1, label="Quantity")
    note = forms.CharField(required=False, max_length=255)
