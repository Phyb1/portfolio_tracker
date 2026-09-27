import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from apps.subscriptions.models import EcocashPayment, Subscription

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    return User.objects.create_user(username="investor", password="pass12345")


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(username="admin", password="pass12345", email="a@a.com")


def test_subscription_reference_is_unique(user):
    sub1 = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="ecocash_manual")
    sub2 = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="ecocash_manual")
    assert sub1.reference != sub2.reference


def test_activate_sets_period_and_status(user, settings):
    settings.SUBSCRIPTION_PERIOD_DAYS = 90
    sub = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="paynow")
    sub.activate()
    assert sub.status == Subscription.STATUS_ACTIVE
    assert (sub.period_end - sub.period_start).days == 90


def test_ecocash_confirm_activates_subscription(user, admin_user):
    sub = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="ecocash_manual")
    payment = EcocashPayment.objects.create(subscription=sub, sender_phone_number="0771234567")

    payment.confirm(admin_user=admin_user)

    sub.refresh_from_db()
    payment.refresh_from_db()
    assert payment.status == EcocashPayment.STATUS_CONFIRMED
    assert sub.status == Subscription.STATUS_ACTIVE
    assert user.profile.has_active_subscription is True


def test_ecocash_reject_does_not_activate_subscription(user, admin_user):
    sub = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="ecocash_manual")
    payment = EcocashPayment.objects.create(subscription=sub)

    payment.reject(admin_user=admin_user, note="Amount doesn't match")

    sub.refresh_from_db()
    assert payment.status == EcocashPayment.STATUS_REJECTED
    assert sub.status == Subscription.STATUS_PENDING


def test_expired_subscription_does_not_grant_premium_access(user):
    sub = Subscription.objects.create(user=user, amount_usd="5.00", payment_method="ecocash_manual")
    sub.activate()
    sub.period_end = timezone.now() - timezone.timedelta(days=1)
    sub.save()

    user.profile.trial_ends_at = timezone.now() - timezone.timedelta(days=1)
    user.profile.save()

    assert user.profile.has_premium_access is False
