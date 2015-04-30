# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0006_initiative_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='datetime',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='idea',
            name='datetime',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='vote',
            name='datetime',
            field=models.DateTimeField(),
        ),
    ]
