# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.IntegerField()),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.IntegerField()),
                ('text', models.TextField()),
                ('datetime', models.CharField(max_length=50)),
                ('positive_votes', models.IntegerField()),
                ('negative_votes', models.IntegerField(null=True)),
                ('comments', models.IntegerField(null=True)),
                ('parent_type', models.CharField(max_length=50)),
                ('parent_id', models.IntegerField(max_length=50)),
                ('url', models.URLField()),
            ],
        ),
        migrations.CreateModel(
            name='Idea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.IntegerField()),
                ('title', models.CharField(max_length=100)),
                ('text', models.TextField()),
                ('datetime', models.CharField(max_length=50)),
                ('positive_votes', models.IntegerField()),
                ('negative_votes', models.IntegerField(null=True)),
                ('comments', models.IntegerField(null=True)),
                ('url', models.URLField()),
                ('campaign', models.ForeignKey(to='ideascale.Campaign')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=50)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ideascale_id', models.IntegerField()),
                ('value', models.IntegerField()),
                ('datetime', models.CharField(max_length=50)),
                ('author', models.ForeignKey(to='ideascale.Author')),
                ('idea', models.ForeignKey(to='ideascale.Idea')),
            ],
        ),
        migrations.AlterField(
            model_name='initiative',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddField(
            model_name='idea',
            name='location',
            field=models.ForeignKey(to='ideascale.Location'),
        ),
        migrations.AddField(
            model_name='idea',
            name='user',
            field=models.ForeignKey(to='ideascale.Author'),
        ),
        migrations.AddField(
            model_name='comment',
            name='location',
            field=models.ForeignKey(to='ideascale.Location'),
        ),
        migrations.AddField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(to='ideascale.Author'),
        ),
    ]
