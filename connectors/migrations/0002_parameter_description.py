# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='description',
            field=models.CharField(max_length=150, null=True, blank=True),
        ),
    ]
