from django.urls import (
    path,
    re_path,
)

from . import (
    feeds,
    views,
)

app_name = "feed"

urlpatterns = [
    path("article/atom/<str:pk>", feeds.ArticleFeed()),
    path(
        "image/<str:name>/<int:pk>",
        views.ImageView.as_view(),
        name="image",
    ),
    path(
        "receiver",
        views.ReceiverView.as_view(),
        name="receiver",
    ),
]
