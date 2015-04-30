# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0002_parameter_description'),
    ]

    operations = [
        migrations.RenameField(
            model_name='callback',
            old_name='type',
            new_name='method',
        ),
    ]
