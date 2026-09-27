from django.contrib import admin

from .models import Entry, Holding


class EntryInline(admin.TabularInline):
    model = Entry
    extra = 0
    readonly_fields = ("date",)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("user", "counter", "quantity", "updated_at")
    list_filter = ("counter__exchange",)
    search_fields = ("user__username", "counter__symbol")
    inlines = [EntryInline]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("holding", "quantity_change", "date", "note")
    list_filter = ("date",)
