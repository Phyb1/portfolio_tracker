from django.urls import path

from . import views

app_name = "markets"

urlpatterns = [
    path("", views.market_summary, name="summary"),
    path("<str:exchange_code>/<str:symbol>/", views.counter_detail, name="counter_detail"),
    path("<str:exchange_code>/<str:symbol>/chart-data/", views.counter_chart_data, name="counter_chart_data"),
]
