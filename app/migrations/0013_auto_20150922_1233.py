# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0012_auto_20150921_1503'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='exist',
            new_name='exist_cp',
        ),
        migrations.RenameField(
            model_name='idea',
            old_name='exist',
            new_name='exist_cp',
        ),
        migrations.RenameField(
            model_name='vote',
            old_name='exist',
            new_name='exist_cp',
        ),
        migrations.AddField(
            model_name='comment',
            name='exist_sn',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='idea',
            name='exist_sn',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='exist_sn',
            field=models.BooleanField(default=True),
        ),
    ]
