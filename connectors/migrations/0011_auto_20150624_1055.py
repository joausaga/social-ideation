# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0010_auto_20150513_1724'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialnetworkconnector',
            name='consumer_key',
        ),
        migrations.RemoveField(
            model_name='socialnetworkconnector',
            name='consumer_secret',
        ),
        migrations.RemoveField(
            model_name='socialnetworkconnector',
            name='token',
        ),
        migrations.RemoveField(
            model_name='socialnetworkconnector',
            name='token_secret',
        ),
        migrations.AddField(
            model_name='socialnetworkconnector',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
