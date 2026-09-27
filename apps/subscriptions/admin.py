from django.contrib import admin

from .models import EcocashPayment, PaynowPayment, Subscription


class EcocashPaymentInline(admin.StackedInline):
    model = EcocashPayment
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "reference", "amount_usd", "payment_method", "status", "period_end")
    list_filter = ("status", "payment_method")
    search_fields = ("user__username", "reference")
    inlines = [EcocashPaymentInline]


@admin.register(EcocashPayment)
class EcocashPaymentAdmin(admin.ModelAdmin):
    list_display = ("subscription", "sender_phone_number", "status", "confirmed_by", "confirmed_at")
    list_filter = ("status",)
    actions = ["confirm_selected"]

    @admin.action(description="Confirm selected EcoCash payments and activate subscriptions")
    def confirm_selected(self, request, queryset):
        for payment in queryset.filter(status=EcocashPayment.STATUS_PENDING):
            payment.confirm(admin_user=request.user)
        self.message_user(request, f"Confirmed {queryset.count()} payment(s).")


@admin.register(PaynowPayment)
class PaynowPaymentAdmin(admin.ModelAdmin):
    list_display = ("subscription", "status", "created_at")
    list_filter = ("status",)
