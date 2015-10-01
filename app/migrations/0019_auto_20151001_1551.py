# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_auto_20150924_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='read_permissions',
            field=models.BooleanField(default=False, editable=False),
        ),
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='write_permissions',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
