# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20150521_1847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='cp_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='sn_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='cp_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='sn_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='vote',
            name='cp_id',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='vote',
            name='datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='vote',
            name='sn_id',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
