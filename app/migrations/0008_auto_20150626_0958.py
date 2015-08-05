# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20150625_0952'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='inconsistent',
        ),
        migrations.RemoveField(
            model_name='idea',
            name='inconsistent',
        ),
        migrations.RemoveField(
            model_name='vote',
            name='inconsistent',
        ),
        migrations.AddField(
            model_name='author',
            name='payload',
            field=models.TextField(null=True, editable=False),
        ),
    ]
