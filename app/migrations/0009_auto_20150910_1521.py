# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_auto_20150910_1307'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='socialnetworkappcommunity',
            name='uri',
        ),
        migrations.AlterField(
            model_name='socialnetworkappcommunity',
            name='external_id',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='socialnetworkappcommunity',
            name='members',
            field=models.ManyToManyField(to='app.SocialNetworkAppUser', editable=False),
        ),
        migrations.AlterField(
            model_name='socialnetworkappcommunity',
            name='token',
            field=models.CharField(max_length=300, null=True, editable=False),
        ),
    ]
