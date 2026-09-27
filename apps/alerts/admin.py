from django.contrib import admin

from .models import PriceAlert


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "counter", "direction", "target_price", "is_active", "triggered_at")
    list_filter = ("direction", "is_active", "counter__exchange")
    search_fields = ("user__username", "counter__symbol")
