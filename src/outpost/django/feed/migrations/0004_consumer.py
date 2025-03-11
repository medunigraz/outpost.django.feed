# Generated by Django 2.2.28 on 2025-03-11 10:48

import django.contrib.postgres.fields
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("feed", "0003_auto_20231124_1606"),
    ]

    operations = [
        migrations.CreateModel(
            name="Consumer",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=256)),
                (
                    "roles",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(max_length=32),
                        blank=True,
                        null=True,
                        size=None,
                    ),
                ),
            ],
        ),
    ]
