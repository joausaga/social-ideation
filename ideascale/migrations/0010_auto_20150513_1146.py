# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0009_auto_20150430_0006'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TestingParameters',
            new_name='TestingParameter',
        ),
    ]
