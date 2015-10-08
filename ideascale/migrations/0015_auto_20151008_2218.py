# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0014_auto_20150910_1548'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='location',
            field=models.ForeignKey(to='ideascale.Location', null=True),
        ),
    ]
