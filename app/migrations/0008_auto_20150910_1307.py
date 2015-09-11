# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0007_auto_20150908_1518'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialNetworkAppCommunity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_id', models.CharField(max_length=50, editable=False)),
                ('name', models.CharField(max_length=50)),
                ('uri', models.URLField()),
                ('token', models.CharField(max_length=300, null=True, blank=True)),
                ('type', models.CharField(default=b'en', max_length=5, choices=[(b'page', b'Page'), (b'group', b'Group'), (b'user_account', b'User Account')])),
                ('members', models.ManyToManyField(to='app.SocialNetworkAppUser')),
            ],
        ),
        migrations.RemoveField(
            model_name='socialnetworkapp',
            name='page_id',
        ),
        migrations.RemoveField(
            model_name='socialnetworkapp',
            name='page_token',
        ),
        migrations.AddField(
            model_name='socialnetworkapp',
            name='redirect_uri',
            field=models.URLField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='socialnetworkapp',
            name='community',
            field=models.ForeignKey(default=None, to='app.SocialNetworkAppCommunity'),
        ),
    ]
