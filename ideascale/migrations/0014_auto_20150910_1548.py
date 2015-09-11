# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0013_auto_20150828_1654'),
    ]

    operations = [
        migrations.AddField(
            model_name='author',
            name='source',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='author',
            name='email',
            field=models.EmailField(max_length=254, null=True),
        ),
    ]
