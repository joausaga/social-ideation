# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_socialnetwork_blocked'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetwork',
            name='callback_real_time_updates',
            field=models.URLField(null=True),
        ),
        migrations.AddField(
            model_name='socialnetwork',
            name='field_real_time_updates',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='socialnetwork',
            name='object_real_time_updates',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='socialnetwork',
            name='token_real_time_updates',
            field=models.CharField(max_length=100, null=True, editable=False),
        ),
    ]
