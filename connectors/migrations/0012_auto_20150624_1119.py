# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0011_auto_20150624_1055'),
    ]

    operations = [
        migrations.RenameField(
            model_name='socialnetworkconnector',
            old_name='connector_package',
            new_name='connector_module',
        ),
    ]
