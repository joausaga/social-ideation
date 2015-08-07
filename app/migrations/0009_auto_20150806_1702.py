# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20150626_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='initiative',
            name='platform',
            field=models.ForeignKey(editable=False, to='app.ConsultationPlatform'),
        ),
    ]
