import urllib.parse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt

from .forms import EcocashPaymentForm
from .models import EcocashPayment, PaynowPayment, Subscription
from .services.paynow import check_transaction_status, initiate_mobile_payment


@login_required
def plans(request):
    context = {
        "price": settings.SUBSCRIPTION_PRICE_USD,
        "period_days": settings.SUBSCRIPTION_PERIOD_DAYS,
        "profile": request.user.profile,
    }
    return render(request, "subscriptions/plans.html", context)


@login_required
def start_ecocash(request):
    subscription = Subscription.objects.create(
        user=request.user,
        amount_usd=settings.SUBSCRIPTION_PRICE_USD,
        payment_method=Subscription.METHOD_ECOCASH_MANUAL,
    )
    ecocash_payment = EcocashPayment.objects.create(subscription=subscription)

    whatsapp_text = (
        f"Hi PHYB, I've sent ${settings.SUBSCRIPTION_PRICE_USD} EcoCash for my "
        f"Portfolio Tracker subscription. Reference: {subscription.reference}. "
        "Attaching my payment screenshot."
    )
    whatsapp_url = (
        f"https://wa.me/{settings.WHATSAPP_BUSINESS_NUMBER}"
        f"?text={urllib.parse.quote(whatsapp_text)}"
    )

    context = {
        "subscription": subscription,
        "ecocash_payment": ecocash_payment,
        "ecocash_number": settings.ECOCASH_RECEIVE_NUMBER,
        "ecocash_name": settings.ECOCASH_RECEIVE_NAME,
        "whatsapp_url": whatsapp_url,
        "form": EcocashPaymentForm(instance=ecocash_payment),
    }
    return render(request, "subscriptions/ecocash_instructions.html", context)


@login_required
def confirm_ecocash_sender(request, reference):
    """Optional: let the user record which number they paid from, to speed up admin matching."""
    subscription = get_object_or_404(Subscription, reference=reference, user=request.user)
    ecocash_payment = subscription.ecocash_payment
    if request.method == "POST":
        form = EcocashPaymentForm(request.POST, instance=ecocash_payment)
        if form.is_valid():
            form.save()
            messages.success(
                request, "Thanks — we'll confirm your payment once we match it on WhatsApp."
            )
            return redirect("subscriptions:plans")
    else:
        form = EcocashPaymentForm(instance=ecocash_payment)
    return render(
        request,
        "subscriptions/ecocash_instructions.html",
        {"subscription": subscription, "ecocash_payment": ecocash_payment, "form": form},
    )


@login_required
def start_paynow(request):
    subscription = Subscription.objects.create(
        user=request.user,
        amount_usd=settings.SUBSCRIPTION_PRICE_USD,
        payment_method=Subscription.METHOD_PAYNOW,
    )
    result = initiate_mobile_payment(
        reference=subscription.reference,
        amount=str(settings.SUBSCRIPTION_PRICE_USD),
        email=request.user.email or "no-reply@phyb.co.zw",
        phone=request.user.profile.phone_number or "",
    )

    if not result.success:
        subscription.delete()
        messages.error(request, f"Paynow payment could not be started: {result.error}")
        return redirect("subscriptions:plans")

    PaynowPayment.objects.create(
        subscription=subscription, poll_url=result.poll_url, status="sent"
    )

    if result.redirect_url:
        return redirect(result.redirect_url)
    messages.info(request, "Payment initiated — check your phone to approve it.")
    return redirect("subscriptions:plans")


@csrf_exempt
def paynow_result(request):
    """Paynow server-to-server callback (resulturl). No auth — Paynow calls this directly."""
    reference = request.POST.get("reference")
    if not reference:
        return HttpResponse(status=400)

    subscription = Subscription.objects.filter(reference=reference).first()
    if not subscription or not hasattr(subscription, "paynow_payment"):
        return HttpResponse(status=404)

    paynow_payment = subscription.paynow_payment
    status = check_transaction_status(paynow_payment.poll_url) if paynow_payment.poll_url else "Unknown"

    if status.lower() == "paid" and subscription.status != Subscription.STATUS_ACTIVE:
        paynow_payment.mark_paid()

    return HttpResponse("OK")


@login_required
def paynow_return(request):
    messages.info(request, "If your payment succeeded, your subscription will activate shortly.")
    return redirect("subscriptions:plans")
