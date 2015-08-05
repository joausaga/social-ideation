# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0010_auto_20150513_1146'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='sync',
            field=models.BooleanField(default=False),
        ),
    ]
