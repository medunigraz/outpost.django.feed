import logging
import uuid
from io import BytesIO

import iso8601
import requests
from django.contrib.gis.db import models
from django.contrib.postgres.fields import (
    ArrayField,
    HStoreField,
    JSONField,
)
from django.urls import reverse
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
    roles = ArrayField(models.CharField(max_length=32), null=True, blank=True)
    flags = HStoreField(null=True, blank=True)
    original = JSONField(null=True, blank=True)

    class Meta:
        ordering = ("created",)

    class Mapping:
        @staticmethod
        def body(data):
            return data.get("entry").get("description")

        @staticmethod
        def created(data):
            return iso8601.parse_date(data.get("entry").get("createdAt"))

        @staticmethod
        def updated(data):
            return iso8601.parse_date(data.get("entry").get("updatedAt"))

        @staticmethod
        def published(data):
            date = data.get("entry").get("publishedAt")
            if date:
                return iso8601.parse_date(date)

        @staticmethod
        def image(data):
            return data.get("entry").get("titleImage").get("url")

        @staticmethod
        def roles(data):
            return [data.get("entry").get("role").get("value")]

        @staticmethod
        def flags(data):
            return {"kages": data.get("entry").get("exportToKAGes")}

        @staticmethod
        def original(data):
            return data

    def __str__(self):
        return self.title

    @memoize(timeout=settings.FEED_CACHE_IMAGE_TIMEOUT)
    def get_image(self):
        if self.image:
            url = URL(settings.FEED_ARTICLE_IMAGE_URL).path(self.image)
            try:
                with requests.get(
                    url.as_string(), cookies=settings.FEED_ARTICLE_IMAGE_COOKIES
                ) as resp:
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


class Consumer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=256)
    roles = ArrayField(models.CharField(max_length=32), null=True, blank=True)

    def __str__(self):
        return self.name
