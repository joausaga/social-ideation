# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20150817_1530'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetworkapp',
            name='last_real_time_update_sig',
            field=models.CharField(max_length=100, null=True, editable=False),
        ),
    ]
