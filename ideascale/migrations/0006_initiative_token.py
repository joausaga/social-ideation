# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0005_auto_20150429_1047'),
    ]

    operations = [
        migrations.AddField(
            model_name='initiative',
            name='token',
            field=models.CharField(default='a', max_length=255),
            preserve_default=False,
        ),
    ]
