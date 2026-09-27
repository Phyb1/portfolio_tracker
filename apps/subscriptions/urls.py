from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.plans, name="plans"),
    path("ecocash/start/", views.start_ecocash, name="start_ecocash"),
    path("ecocash/<str:reference>/", views.confirm_ecocash_sender, name="confirm_ecocash_sender"),
    path("paynow/start/", views.start_paynow, name="start_paynow"),
    path("paynow/result/", views.paynow_result, name="paynow_result"),
    path("paynow/return/", views.paynow_return, name="paynow_return"),
]
