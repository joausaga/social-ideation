# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20150624_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='inconsistent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='idea',
            name='inconsistent',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='inconsistent',
            field=models.BooleanField(default=False),
        ),
    ]
