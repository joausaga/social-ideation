# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_auto_20150910_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetworkappcommunity',
            name='url',
            field=models.URLField(default=None),
        ),
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='url',
            field=models.URLField(null=True, blank=True),
        ),
    ]
