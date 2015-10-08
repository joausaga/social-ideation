# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0019_auto_20151001_1551'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='notification_emails',
            field=models.BooleanField(default=False),
        ),
    ]
