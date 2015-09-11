# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20150910_1629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialnetworkapp',
            name='access_token',
        ),
        migrations.AddField(
            model_name='socialnetworkapp',
            name='app_access_token',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
    ]
