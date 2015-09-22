# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0013_auto_20150922_1233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='exist_cp',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='exist_sn',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='idea',
            name='exist_cp',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='idea',
            name='exist_sn',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='vote',
            name='exist_cp',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='vote',
            name='exist_sn',
            field=models.BooleanField(default=False),
        ),
    ]
