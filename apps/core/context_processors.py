from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
    }
