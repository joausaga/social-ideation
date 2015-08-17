# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0013_socialnetworkconnector_url_subscriptions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialnetworkconnector',
            name='url_subscriptions',
        ),
    ]
