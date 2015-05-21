# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0008_auto_20150430_0849'),
    ]

    operations = [
        migrations.AlterField(
            model_name='callback',
            name='format',
            field=models.CharField(max_length=50, choices=[(b'json', b'JSON'), (b'xml', b'XML'), (b'txt', b'TXT')]),
        ),
    ]
