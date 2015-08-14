# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0012_auto_20150624_1119'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetworkconnector',
            name='url_subscriptions',
            field=models.URLField(null=True),
        ),
    ]
