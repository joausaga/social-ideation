# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0007_urlcallback_ok'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='urlcallback',
            name='ok',
        ),
        migrations.AddField(
            model_name='urlcallback',
            name='status',
            field=models.CharField(default=b'untested', max_length=50, choices=[(b'ok', b'Ok'), (b'untested', b'Untested'), (b'failure', b'Failure')]),
        ),
    ]
