from django import forms

from apps.markets.models import Counter

from .models import PriceAlert


class PriceAlertForm(forms.ModelForm):
    counter = forms.ModelChoiceField(
        queryset=Counter.objects.filter(status=Counter.STATUS_ACTIVE).select_related("exchange")
    )

    class Meta:
        model = PriceAlert
        fields = ["counter", "target_price", "direction"]
