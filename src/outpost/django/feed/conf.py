from appconf import AppConf
from django.conf import settings


class FeedAppConf(AppConf):
    CACHE_IMAGE_TIMEOUT = 3600
    ARTICLE_ROLES = []
    ARTICLE_DESCRIPTION = ""
    ARTICLE_COPYRIGHT = ""
    ARTICLE_URL = ""
    ARTICLE_ITEMS = 20
    ARTICLE_ITEM_URL = ""

    class Meta:
        prefix = "feed"
