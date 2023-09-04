import logging

from braces.views import (
    CsrfExemptMixin,
    LoginRequiredMixin,
)
from django.apps import apps
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
)
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import cache_page
from django.views.generic import View
from rest_framework import (
    authentication,
    permissions,
)
from rest_framework.views import APIView

from . import models
from .conf import settings

logger = logging.getLogger(__name__)


@method_decorator(cache_page(settings.FEED_CACHE_IMAGE_TIMEOUT), name="dispatch")
class ImageView(View):
    def get(self, request, name, pk):
        try:
            model = apps.get_model("feed", name)
        except LookupError as e:
            return HttpResponseNotFound(str(e))
        obj = get_object_or_404(model, pk=pk)
        if not hasattr(obj, "get_image"):
            return HttpResponseNotFound(_("Model does not support image publishing."))
        img = obj.get_image()
        if not img:
            return HttpResponseNotFound()
        response = HttpResponse()
        img.save(response, format="webp")
        response["Content-Type"] = "image/webp"
        response["Cache-Control"] = "private,max-age=604800"
        return response


class ReceiverView(APIView):

    authentication_classes = [
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
    ]
    permission_classes = [permissions.IsAuthenticated]

    model_map = {
        "api::infocenter-article.infocenter-article": models.Article,
    }

    def post(self, request):
        uid = request.data.get("uid")
        if uid not in self.model_map:
            return HttpResponseBadRequest(_("Unknown model specified: {}").format(uid))
        model = self.model_map.get(uid)
        entry = request.data.get("entry", dict())
        if not model.can_receive(entry):
            return HttpResponseBadRequest(_("Entry is not applicable for storage"))
        event = request.data.get("event")
        if not event:
            return HttpResponseBadRequest(_("No applicable event found"))
        etype, action = event.split(".")
        handler = getattr(self, f"handle_{action}", None)
        if not handler:
            return HttpResponseBadRequest(_("No matching handler found"))
        status = handler(model, entry)
        return HttpResponse(status=status)

    def handle_create(self, model, entry):
        defaults = dict()
        for field, value in entry.items():
            if hasattr(model, "Mapping") and (
                converter := getattr(model.Mapping, field, None)
            ):
                k, value = converter(value)
                if k:
                    field = k
            if not hasattr(model, field):
                continue
            defaults[field] = value
        oid = entry.get(model._meta.pk.attname)
        obj, created = model.objects.update_or_create(pk=oid, defaults=defaults)
        if created:
            logger.info(f"Created new {model}: {obj}")
            return 201
        else:
            logger.info(f"Updated existing {model}: {obj}")
            return 204

    def handle_update(self, model, entry):
        return self.handle_create(model, entry)

    def handle_publish(self, model, entry):
        return self.handle_create(model, entry)

    def handle_delete(self, model, entry):
        oid = entry.get(model._meta.pk.attname)
        obj = model.objects.get(pk=oid)
        obj.delete()
        logger.info(f"Deleted {model}: {obj}")
        return 204

    def handle_unpublish(self, model, entry):
        return self.handle_delete(model, entry)
