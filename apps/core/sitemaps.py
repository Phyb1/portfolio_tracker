from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.markets.models import Counter


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "daily"

    def items(self):
        return ["core:home", "markets:summary", "accounts:signup"]

    def location(self, item):
        return reverse(item)


class CounterSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return Counter.objects.filter(status=Counter.STATUS_ACTIVE).select_related("exchange")

    def location(self, counter):
        return reverse("markets:counter_detail", args=[counter.exchange.code, counter.symbol])


sitemaps = {"static": StaticViewSitemap, "counters": CounterSitemap}
