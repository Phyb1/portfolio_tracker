from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from freezegun import freeze_time

pytestmark = pytest.mark.django_db


def test_profile_auto_created_on_user_creation():
    user = User.objects.create_user(username="tendai", password="pass12345")
    assert hasattr(user, "profile")


def test_trial_ends_at_defaults_to_settings_trial_period(settings):
    settings.TRIAL_PERIOD_DAYS = 30
    with freeze_time("2026-01-01 12:00:00"):
        user = User.objects.create_user(username="rutendo", password="pass12345")
    expected = timezone.datetime(2026, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
    assert user.profile.trial_ends_at == expected


def test_is_trial_active_true_within_window():
    user = User.objects.create_user(username="farai", password="pass12345")
    assert user.profile.is_trial_active is True
    assert user.profile.has_premium_access is True


def test_is_trial_active_false_after_expiry():
    user = User.objects.create_user(username="tapiwa", password="pass12345")
    user.profile.trial_ends_at = timezone.now() - timedelta(days=1)
    user.profile.save()
    assert user.profile.is_trial_active is False


def test_days_left_in_trial_never_negative():
    user = User.objects.create_user(username="chipo", password="pass12345")
    user.profile.trial_ends_at = timezone.now() - timedelta(days=5)
    user.profile.save()
    assert user.profile.days_left_in_trial == 0
