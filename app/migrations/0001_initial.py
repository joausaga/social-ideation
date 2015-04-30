# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('hashtag', models.CharField(help_text=b"Max length 14 characters (do not include '#')", max_length=14)),
            ],
        ),
        migrations.CreateModel(
            name='IdeationCampaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='IdeationInitiatve',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('organizer', models.CharField(max_length=50)),
                ('language', models.CharField(max_length=3, choices=[(b'en', b'English'), (b'es', b'Spanish'), (b'it', b'Italian')])),
                ('url', models.URLField()),
                ('users', models.IntegerField(default=0, editable=False)),
                ('ideas', models.IntegerField(default=0, editable=False)),
                ('votes', models.IntegerField(default=0, editable=False)),
                ('comments', models.IntegerField(default=0, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='IdeationPlatform',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('url', models.URLField(null=True, blank=True)),
                ('connector', models.OneToOneField(to='connectors.Connector')),
            ],
        ),
        migrations.CreateModel(
            name='Initiative',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hashtag', models.CharField(help_text=b"Max length 14 characters (do not include '#')", unique=True, max_length=14)),
                ('ideation_initiative', models.ForeignKey(to='app.IdeationInitiatve')),
            ],
        ),
        migrations.CreateModel(
            name='SocialNetwork',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('url', models.URLField(null=True, blank=True)),
                ('connector', models.OneToOneField(to='connectors.SocialNetworkConnector')),
            ],
        ),
        migrations.AddField(
            model_name='initiative',
            name='social_network',
            field=models.ForeignKey(to='app.SocialNetwork'),
        ),
        migrations.AddField(
            model_name='ideationinitiatve',
            name='platform',
            field=models.OneToOneField(to='app.IdeationPlatform'),
        ),
        migrations.AddField(
            model_name='ideationcampaign',
            name='ideation_initiative',
            field=models.ForeignKey(to='app.IdeationInitiatve'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='initiative',
            field=models.ForeignKey(to='app.Initiative'),
        ),
    ]
