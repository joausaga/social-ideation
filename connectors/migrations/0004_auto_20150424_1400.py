# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0003_auto_20150423_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='basicattribute',
            name='empty',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='composedattribute',
            name='empty',
            field=models.BooleanField(default=False),
        ),
    ]
