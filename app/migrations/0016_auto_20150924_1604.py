# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_socialnetworkappcommunity_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='auto',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='socialnetworkappuser',
            name='access_token',
            field=models.CharField(max_length=300),
        ),
        migrations.AlterField(
            model_name='socialnetworkappuser',
            name='email',
            field=models.EmailField(max_length=254),
        ),
        migrations.AlterField(
            model_name='socialnetworkappuser',
            name='external_id',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='socialnetworkappuser',
            name='snapp',
            field=models.ForeignKey(to='app.SocialNetworkApp'),
        ),
    ]
