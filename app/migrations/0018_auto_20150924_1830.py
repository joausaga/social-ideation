# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_auto_20150924_1740'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autocomment',
            name='datetime',
        ),
        migrations.RemoveField(
            model_name='socialnetworkappcommunity',
            name='admin',
        ),
        migrations.AddField(
            model_name='socialnetworkappcommunity',
            name='admins',
            field=models.ManyToManyField(related_name='SocialNetworkAppAdmin', to='app.SocialNetworkAppUser'),
        ),
    ]
