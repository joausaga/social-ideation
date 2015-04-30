# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0004_auto_20150424_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='connector',
            name='auth_header',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='connector',
            name='auth_token',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='connector',
            name='authentication',
            field=models.BooleanField(default=False),
        ),
    ]
