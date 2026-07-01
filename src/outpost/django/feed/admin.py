from django.contrib import admin
from . import models


@admin.register(models.Consumer)
class ConsumerAdmin(admin.ModelAdmin):
    pass
