from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "trial_ends_at", "is_trial_active", "has_active_subscription")
    search_fields = ("user__username", "user__email", "phone_number")
    readonly_fields = ("trial_started_at",)
