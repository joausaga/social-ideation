# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20150814_1730'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetwork',
            name='subscribed_read_time_updates',
            field=models.BooleanField(default=False),
        ),
    ]
