from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    return render(request, "core/home.html")


def robots_txt(request):
    lines = [
        "User-Agent: *",
        "Allow: /",
        f"Sitemap: https://{settings.SITE_DOMAIN}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
