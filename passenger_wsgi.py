"""
Entry point cPanel/Passenger looks for. Mirrors the pattern used across
other PHYB deployments: import the real WSGI app from config.wsgi.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")

from config.wsgi import application  # noqa: E402,F401
