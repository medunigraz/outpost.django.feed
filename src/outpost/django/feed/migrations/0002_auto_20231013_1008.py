# Generated by Django 2.2.28 on 2023-10-13 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feed', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='body',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='article',
            name='published',
            field=models.DateTimeField(null=True),
        ),
    ]
