# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_auto_20150910_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='social_network',
            field=models.ForeignKey(to='app.SocialNetworkApp', null=True),
        ),
    ]
