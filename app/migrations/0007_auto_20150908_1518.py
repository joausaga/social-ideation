# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_auto_20150825_1513'),
    ]

    operations = [
        migrations.CreateModel(
            name='SocialNetworkAppUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_id', models.CharField(max_length=50, editable=False)),
                ('email', models.EmailField(max_length=254, editable=False)),
                ('access_token', models.CharField(max_length=300, editable=False)),
                ('access_token_exp', models.DateTimeField(editable=False)),
            ],
        ),
        migrations.AlterField(
            model_name='author',
            name='social_network',
            field=models.ForeignKey(to='app.SocialNetworkAppUser', null=True),
        ),
        migrations.AlterField(
            model_name='socialnetworkapp',
            name='page_id',
            field=models.CharField(help_text=b'Id of the page/group/account used to hold the content generate in the consultation platform', max_length=50, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='socialnetworkappuser',
            name='snapp',
            field=models.ForeignKey(editable=False, to='app.SocialNetworkApp'),
        ),
    ]
