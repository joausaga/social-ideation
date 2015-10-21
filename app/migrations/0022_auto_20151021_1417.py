# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0021_auto_20151008_1616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='campaign',
            name='hashtag',
            field=models.CharField(help_text=b"Max length 20 characters (do not include '#')", max_length=20, null=True),
        ),
    ]
