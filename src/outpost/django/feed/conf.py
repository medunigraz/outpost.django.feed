from appconf import AppConf
from django.conf import settings


class FeedAppConf(AppConf):
    CACHE_IMAGE_TIMEOUT = 3600
    ARTICLE_DESCRIPTION = ""
    ARTICLE_COPYRIGHT = ""
    ARTICLE_URL = ""
    ARTICLE_ITEMS = 20
    ARTICLE_ITEM_URL = ""
    ARTICLE_IMAGE_URL = ""
    ARTICLE_IMAGE_HEADERS = dict()

    class Meta:
        prefix = "feed"
