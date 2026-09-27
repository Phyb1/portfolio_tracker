from django.urls import path

from . import views

app_name = "alerts"

urlpatterns = [
    path("", views.AlertListView.as_view(), name="list"),
    path("new/", views.AlertCreateView.as_view(), name="new"),
    path("<int:alert_id>/delete/", views.delete_alert, name="delete"),
]
