# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_auto_20150924_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sn_id', models.CharField(max_length=100)),
                ('datetime', models.DateTimeField(null=True)),
                ('parent_idea', models.CharField(max_length=100)),
                ('exist', models.BooleanField(default=True)),
                ('author', models.ForeignKey(to='app.SocialNetworkAppUser')),
            ],
        ),
        migrations.RemoveField(
            model_name='comment',
            name='auto',
        ),
    ]
