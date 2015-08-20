# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0011_author_sync'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='code',
            field=models.CharField(max_length=100, unique=True, null=True),
        ),
    ]
