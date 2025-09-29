import json
from base64 import b64encode

import bs4
from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from purl import URL

from . import models


class FeedCache:
    lifetime = 1

    def __call__(self, request, *args, **kwargs):
        cache_key = self.get_cache_key(*args, **kwargs)
        response = cache.get(cache_key)

        if response is None:
            response = super().__call__(request, *args, **kwargs)
            cache.set(cache_key, response, self.lifetime)

        return response

    def get_cache_key(self, *args, **kwargs):
        return "%s-%s" % (
            self.__class__.__name__,
            "/".join(["%s,%s" % (key, val) for key, val in kwargs.items()]),
        )


class ArticleFeed(FeedCache, Feed):
    title = _("Article")
    link = settings.FEED_ARTICLE_URL
    description = settings.FEED_ARTICLE_DESCRIPTION
    item_copyright = settings.FEED_ARTICLE_COPYRIGHT
    item_guid_is_permalink = False
    item_enclosure_mime_type = "image/webp"

    def get_object(self, request, pk):
        return models.Consumer.objects.get(pk=pk)

    def items(self, obj):
        return models.Article.objects.filter(
            published__isnull=False, roles__overlap=obj.roles
        ).order_by("-published")[: settings.FEED_ARTICLE_ITEMS]

    def item_title(self, item):
        bs = bs4.BeautifulSoup(item.title, "lxml")
        return bs.text

    def item_description(self, item):
        base_url = URL(settings.FEED_ARTICLE_URL)
        bs = bs4.BeautifulSoup(item.body, "lxml")
        for e in bs.find_all(True, {"style": True}):
            del e.attrs["style"]
        for e in bs.find_all(True, {"href": True}):
            href = URL(e.attrs.get("href"))
            if not href.scheme():
                url = base_url.path(href.path())
                e.attrs["href"] = url.as_string()
        return "".join([str(x) for x in bs.body.children])

    def item_link(self, item):
        payload = json.dumps(
            {"id": item.pk, "type": "STRAPI", "localize": True}
        ).encode("utf-8")
        return (
            URL(settings.FEED_ARTICLE_ITEM_URL)
            .query_param("id", b64encode(payload).decode("utf-8"))
            .as_string()
        )

    def item_guid(self, item):
        return item.pk

    def item_pubdate(self, item):
        return item.published

    def item_updateddate(self, item):
        return item.updated

    def item_enclosure_url(self, item):
        return item.get_image_url()
