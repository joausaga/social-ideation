# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_auto_20150806_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetwork',
            name='blocked',
            field=models.DateTimeField(default=None, null=True, editable=False),
        ),
    ]
