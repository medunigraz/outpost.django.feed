import logging
from functools import partial
from io import BytesIO

import iso8601
import requests
from django.contrib.gis.db import models
from django.contrib.postgres.fields import (
    ArrayField,
    JSONField,
)
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from memoize import memoize
from PIL import (
    Image,
    ImageOps,
    UnidentifiedImageError,
)
from purl import URL

from .conf import settings

logger = logging.getLogger(__name__)


class Article(models.Model):
    id = models.IntegerField(primary_key=True)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    published = models.DateTimeField(null=True)
    title = models.TextField()
    subtitle = models.TextField(null=True)
    teaser = models.TextField()
    body = models.TextField(null=True)
    link = models.URLField(null=True)
    image = models.URLField(null=True)

    class Meta:
        ordering = ("created",)

    @classmethod
    def can_receive(cls, entry):
        return entry.get("role", dict()).get("value") in settings.FEED_ARTICLE_ROLES

    class Mapping:
        @staticmethod
        def description(value):
            return ("body", value)

        @staticmethod
        def createdAt(value):
            return ("created", iso8601.parse_date(value))

        @staticmethod
        def updatedAt(value):
            return ("updated", iso8601.parse_date(value))

        @staticmethod
        def publishedAt(value):
            return ("published", iso8601.parse_date(value))

    def __str__(self):
        return self.title

    @memoize(timeout=settings.FEED_CACHE_IMAGE_TIMEOUT)
    def get_image(self):
        if self.image:
            url = URL(settings.FEED_ARTICLE_IMAGE_URL).path(self.image)
            try:
                with requests.get(url.as_string()) as resp:
                    resp.raise_for_status()
                    return ImageOps.exif_transpose(Image.open(BytesIO(resp.content)))
            except requests.RequestException:
                pass
            except UnidentifiedImageError:
                pass

    def get_image_url(self):
        if self.get_image():
            return reverse(
                "feed:image",
                kwargs={"name": self.__class__.__name__, "pk": self.pk},
            )
