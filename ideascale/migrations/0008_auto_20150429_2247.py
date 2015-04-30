# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0007_auto_20150429_1503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comments',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='negative_votes',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='positive_votes',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='idea',
            name='comments',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='negative_votes',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='positive_votes',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
