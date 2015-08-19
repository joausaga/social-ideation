# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_socialnetworkapp_last_real_time_update_sig'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='language',
            field=models.CharField(default=b'en', max_length=5, choices=[(b'en', b'English'), (b'es', b'Spanish'), (b'it', b'Italian')]),
        ),
        migrations.AddField(
            model_name='socialnetworkapp',
            name='batch_requests',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='socialnetworkapp',
            name='max_batch_requests',
            field=models.IntegerField(null=True, blank=True),
        ),
    ]
