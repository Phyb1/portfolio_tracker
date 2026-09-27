from django.conf import settings
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve as serve_static

from apps.core.sitemaps import sitemaps
from apps.core.views import robots_txt

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("portfolio/", include("apps.portfolio.urls")),
    path("markets/", include("apps.markets.urls")),
    path("billing/", include("apps.subscriptions.urls")),
    path("alerts/", include("apps.alerts.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path(
        "service-worker.js",
        TemplateView.as_view(
            template_name="core/service-worker.js", content_type="application/javascript"
        ),
        name="service_worker",
    ),
]

# Explicit static/media routes (rather than relying solely on STATIC_URL
# prefix matching) because cPanel/Passenger subdirectory deployments strip
# the base path before WSGI sees the request, which otherwise breaks
# WhiteNoise's prefix matching. See README for the LiteSpeed symlink note.
urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % settings.MEDIA_URL.lstrip("/"),
        serve_static,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
