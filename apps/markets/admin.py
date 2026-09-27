from django.contrib import admin

from .models import Counter, Exchange, PriceRecord


@admin.register(Exchange)
class ExchangeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "currency")


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "exchange", "status", "status_effective_date", "moved_to")
    list_filter = ("exchange", "status")
    search_fields = ("symbol", "name")
    autocomplete_fields = ("moved_to",)


@admin.register(PriceRecord)
class PriceRecordAdmin(admin.ModelAdmin):
    list_display = ("counter", "date", "closing_price", "volume", "source")
    list_filter = ("source", "counter__exchange")
    search_fields = ("counter__symbol",)
    date_hierarchy = "date"
