# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0014_auto_20150922_1557'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialnetworkappcommunity',
            name='admin',
            field=models.ForeignKey(related_name='SocialNetworkAppAdmin', default=None, to='app.SocialNetworkAppUser'),
        ),
    ]
