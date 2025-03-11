import logging

from django.apps import apps
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
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
        "infocenter-article": models.Article,
    }

    def post(self, request):
        model_name = request.data.get("model")
        if model_name not in self.model_map:
            logger.warn(f"Unknown model specified: {model_name}")
            return HttpResponseBadRequest(
                _("Unknown model specified: {}").format(model_name)
            )
        model = self.model_map.get(model_name)
        event = request.data.get("event")
        if not event:
            logger.warn("No applicable event found")
            return HttpResponseBadRequest(_("No applicable event found"))
        etype, action = event.split(".")
        handler = getattr(self, f"handle_{action}", None)
        if not handler:
            logger.warn(f"No matching handler found for {action}")
            return HttpResponseBadRequest(_("No matching handler found"))
        return handler(request, model, request.data)

    def synchronize(self, model, data):
        defaults = dict()
        entry = data.get("entry", {})
        for field in model._meta.fields:
            if hasattr(model, "Mapping") and (
                converter := getattr(model.Mapping, field.attname, None)
            ):
                defaults[field.attname] = converter(data)
                continue
            if value := entry.get(field.attname):
                defaults[field.attname] = value
        oid = entry.get(model._meta.pk.attname)
        obj, created = model.objects.update_or_create(pk=oid, defaults=defaults)
        if created:
            logger.info(f"Created new {model}: {obj}")
            return HttpResponse(status=201)
        else:
            logger.info(f"Updated existing {model}: {obj}")
            return HttpResponse(status=204)

    def handle_create(self, request, model, data):
        if not request.user.has_perm(
            f"{model._meta.app_label}.add_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()
        return self.synchronize(model, data)

    def handle_update(self, request, model, data):
        if not request.user.has_perm(
            f"{model._meta.app_label}.change_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()
        return self.synchronize(model, data)

    def handle_publish(self, request, model, data):
        if not request.user.has_perm(
            f"{model._meta.app_label}.change_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()
        return self.synchronize(model, data)

    def desynchronize(self, model, data):
        oid = data.get("entry").get(model._meta.pk.attname)
        obj = model.objects.get(pk=oid)
        obj.delete()
        logger.info(f"Deleted {model}: {obj}")
        return HttpResponse(status=204)

    def handle_unpublish(self, request, model, data):
        if not request.user.has_perm(
            f"{model._meta.app_label}.delete_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()
        return self.desynchronize(model, data)

    def handle_delete(self, request, model, data):
        if not request.user.has_perm(
            f"{model._meta.app_label}.delete_{model._meta.model_name}"
        ):
            return HttpResponseForbidden()
        return self.desynchronize(model, data)
