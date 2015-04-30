# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BasicAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50, choices=[(b'str', b'String'), (b'num', b'Number'), (b'bool', b'Boolean')])),
                ('required', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Callback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('return_type', models.CharField(default=b'set', max_length=50, choices=[(b'set', b'Set'), (b'unit', b'Unit')])),
                ('type', models.CharField(max_length=50, choices=[(b'get', b'GET'), (b'post', b'POST'), (b'delete', b'DELETE')])),
                ('format', models.CharField(max_length=50, choices=[(b'json', b'JSON'), (b'xml', b'XML')])),
                ('required', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='ComposedAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('required', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Connector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='MetaConnector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50, choices=[(b'social_network', b'Social Network'), (b'idea_mgmt', b'Idea Management')])),
                ('callbacks', models.ManyToManyField(to='connectors.Callback')),
            ],
        ),
        migrations.CreateModel(
            name='Object',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('attributes', models.ManyToManyField(to='connectors.BasicAttribute', blank=True)),
                ('composed_attributes', models.ManyToManyField(to='connectors.ComposedAttribute', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Parameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('type', models.CharField(max_length=50, choices=[(b'str', b'String'), (b'num', b'Number'), (b'bool', b'Boolean')])),
                ('required', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='SocialNetworkConnector',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('connector_package', models.CharField(max_length=50)),
                ('connector_class', models.CharField(max_length=50)),
                ('consumer_key', models.CharField(max_length=100)),
                ('consumer_secret', models.CharField(max_length=100)),
                ('token', models.CharField(max_length=100)),
                ('token_secret', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='URLCallback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(null=True)),
                ('callback', models.ForeignKey(to='connectors.Callback')),
            ],
        ),
        migrations.AddField(
            model_name='connector',
            name='meta_connector',
            field=models.ForeignKey(to='connectors.MetaConnector'),
        ),
        migrations.AddField(
            model_name='connector',
            name='url_callback',
            field=models.ManyToManyField(to='connectors.URLCallback'),
        ),
        migrations.AddField(
            model_name='composedattribute',
            name='type',
            field=models.ForeignKey(to='connectors.Object'),
        ),
        migrations.AddField(
            model_name='callback',
            name='params',
            field=models.ManyToManyField(to='connectors.Parameter', blank=True),
        ),
        migrations.AddField(
            model_name='callback',
            name='return_object',
            field=models.ForeignKey(to='connectors.Object'),
        ),
    ]
