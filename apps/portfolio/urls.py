from django.urls import path

from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("add/", views.add_holding, name="add_holding"),
    path("remove/<int:holding_id>/", views.remove_holding, name="remove_holding"),
    path("report/", views.report, name="report"),
    path("price-sheet/", views.PriceSheetView.as_view(), name="price_sheet"),
    path("growth-data/", views.portfolio_growth_data, name="growth_data"),
]
