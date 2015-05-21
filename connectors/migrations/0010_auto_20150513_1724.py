# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0009_auto_20150513_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialnetworkconnector',
            name='consumer_key',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkconnector',
            name='consumer_secret',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkconnector',
            name='token',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkconnector',
            name='token_secret',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
