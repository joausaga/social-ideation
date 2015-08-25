# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20150819_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='field_real_time_updates',
            field=models.CharField(default=b'feed', max_length=50, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='object_real_time_updates',
            field=models.CharField(default=b'page', max_length=100, null=True, blank=True),
            preserve_default=True,
        ),
    ]
