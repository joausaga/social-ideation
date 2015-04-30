# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0006_auto_20150428_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='urlcallback',
            name='ok',
            field=models.BooleanField(default=False),
        ),
    ]
