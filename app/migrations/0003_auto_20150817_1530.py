# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20150817_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='app_secret',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='callback_real_time_updates',
            field=models.URLField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='field_real_time_updates',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='object_real_time_updates',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='page_id',
            field=models.CharField(max_length=50, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='page_token',
            field=models.CharField(max_length=300, null=True, blank=True),
        ),
    ]
