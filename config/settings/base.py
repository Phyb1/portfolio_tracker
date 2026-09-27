"""
Base settings for the Simple Portfolio Tracker project.
Shared across dev / prod / test. Environment-specific values come from .env
via python-decouple so the same codebase deploys unchanged to cPanel.
"""
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.sites",

    # Third party
    "whitenoise.runserver_nostatic",

    # Local apps
    "apps.accounts",
    "apps.markets",
    "apps.portfolio",
    "apps.subscriptions",
    "apps.alerts",
    "apps.core",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.subscriptions.middleware.TrialStatusMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_meta",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.sqlite3"),
        "NAME": config("DB_NAME", default=str(BASE_DIR / "db.sqlite3")),
        "USER": config("DB_USER", default=""),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default=""),
        "PORT": config("DB_PORT", default=""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Harare"
USE_I18N = True
USE_TZ = True

# Static & media — env-configurable so cPanel/Passenger subdirectory
# deployments (which strip path prefixes) can be fixed without code changes.
STATIC_URL = config("STATIC_URL", default="static/")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = config("MEDIA_URL", default="media/")
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "portfolio:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# --- Project-specific settings -------------------------------------------

SITE_NAME = "Simple Portfolio Tracker"
SITE_DOMAIN = config("SITE_DOMAIN", default="localhost:8000")
SITE_DESCRIPTION = (
    "Track your ZSE and VFEX investment portfolio: gains/losses, market "
    "activity, price alerts and growth charts, built for Zimbabwean investors."
)

TRIAL_PERIOD_DAYS = config("TRIAL_PERIOD_DAYS", default=30, cast=int)
SUBSCRIPTION_PRICE_USD = config("SUBSCRIPTION_PRICE_USD", default="5.00")
SUBSCRIPTION_PERIOD_DAYS = config("SUBSCRIPTION_PERIOD_DAYS", default=90, cast=int)

ECOCASH_RECEIVE_NUMBER = config("ECOCASH_RECEIVE_NUMBER", default="")
ECOCASH_RECEIVE_NAME = config("ECOCASH_RECEIVE_NAME", default="PHYB")
WHATSAPP_BUSINESS_NUMBER = config("WHATSAPP_BUSINESS_NUMBER", default="")

PAYNOW_INTEGRATION_ID = config("PAYNOW_INTEGRATION_ID", default="")
PAYNOW_INTEGRATION_KEY = config("PAYNOW_INTEGRATION_KEY", default="")
PAYNOW_RETURN_URL = config("PAYNOW_RETURN_URL", default="")
PAYNOW_RESULT_URL = config("PAYNOW_RESULT_URL", default="")

# Email (used for price alerts)
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="alerts@phyb.co.zw")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{asctime} {levelname} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "apps.markets": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.subscriptions": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.alerts": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
