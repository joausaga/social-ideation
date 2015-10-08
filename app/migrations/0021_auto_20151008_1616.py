# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0020_initiative_notification_emails'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='connector',
            field=models.ForeignKey(to='connectors.SocialNetworkConnector'),
        ),
    ]
