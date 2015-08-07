# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20150806_1702'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='hashtag',
            field=models.CharField(help_text=b"Max length 14 characters (do not include '#')", max_length=14, null=True),
        ),
    ]
