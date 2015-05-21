# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20150513_1515'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_id', models.CharField(max_length=50)),
                ('screen_name', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100, null=True)),
                ('bio', models.TextField(null=True)),
                ('language', models.CharField(max_length=10, null=True)),
                ('zipcode', models.CharField(max_length=10, null=True, blank=True)),
                ('national_id', models.CharField(max_length=20, null=True, blank=True)),
                ('address', models.CharField(max_length=200, null=True, blank=True)),
                ('email', models.EmailField(max_length=254, null=True, blank=True)),
                ('friends', models.IntegerField(default=0, editable=False)),
                ('followers', models.IntegerField(default=0, editable=False)),
                ('groups', models.IntegerField(default=0, editable=False)),
                ('posts_count', models.IntegerField(default=0, editable=False)),
                ('url', models.URLField(null=True, blank=True)),
                ('channel', models.CharField(max_length=50, choices=[(b'consultation_platform', b'Consultation Platform'), (b'social_network', b'Social Network')])),
                ('consultation_platform', models.ForeignKey(to='app.ConsultationPlatform', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sn_id', models.CharField(max_length=50, null=True)),
                ('cp_id', models.CharField(max_length=50, null=True)),
                ('datetime', models.DateTimeField()),
                ('source', models.CharField(max_length=50, choices=[(b'consultation_platform', b'Consultation Platform'), (b'social_network', b'Social Network')])),
                ('payload', models.TextField(null=True, editable=False)),
                ('is_new', models.BooleanField(default=True)),
                ('has_changed', models.BooleanField(default=False)),
                ('exist', models.BooleanField(default=True)),
                ('sync', models.BooleanField(default=False)),
                ('text', models.TextField()),
                ('url', models.URLField(null=True)),
                ('parent', models.CharField(max_length=10, choices=[(b'idea', b'Idea'), (b'comment', b'Comment')])),
                ('positive_votes', models.IntegerField(default=0)),
                ('negative_votes', models.IntegerField(default=0)),
                ('comments', models.IntegerField(default=0)),
                ('author', models.ForeignKey(to='app.Author')),
                ('campaign', models.ForeignKey(to='app.Campaign')),
                ('initiative', models.ForeignKey(to='app.Initiative')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Idea',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sn_id', models.CharField(max_length=50, null=True)),
                ('cp_id', models.CharField(max_length=50, null=True)),
                ('datetime', models.DateTimeField()),
                ('source', models.CharField(max_length=50, choices=[(b'consultation_platform', b'Consultation Platform'), (b'social_network', b'Social Network')])),
                ('payload', models.TextField(null=True, editable=False)),
                ('is_new', models.BooleanField(default=True)),
                ('has_changed', models.BooleanField(default=False)),
                ('exist', models.BooleanField(default=True)),
                ('sync', models.BooleanField(default=False)),
                ('title', models.CharField(max_length=255, null=True)),
                ('text', models.TextField()),
                ('url', models.URLField(null=True)),
                ('re_posts', models.IntegerField(default=0)),
                ('bookmarks', models.IntegerField(default=0)),
                ('positive_votes', models.IntegerField(default=0)),
                ('negative_votes', models.IntegerField(default=0)),
                ('comments', models.IntegerField(default=0)),
                ('author', models.ForeignKey(to='app.Author')),
                ('campaign', models.ForeignKey(to='app.Campaign')),
                ('initiative', models.ForeignKey(to='app.Initiative')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('country', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=50)),
                ('latitude', models.FloatField(null=True)),
                ('longitude', models.FloatField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Vote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sn_id', models.CharField(max_length=50, null=True)),
                ('cp_id', models.CharField(max_length=50, null=True)),
                ('datetime', models.DateTimeField()),
                ('source', models.CharField(max_length=50, choices=[(b'consultation_platform', b'Consultation Platform'), (b'social_network', b'Social Network')])),
                ('payload', models.TextField(null=True, editable=False)),
                ('is_new', models.BooleanField(default=True)),
                ('has_changed', models.BooleanField(default=False)),
                ('exist', models.BooleanField(default=True)),
                ('sync', models.BooleanField(default=False)),
                ('value', models.IntegerField(default=1, choices=[(1, b'Positive'), (-1, b'Negative')])),
                ('parent', models.CharField(max_length=10, choices=[(b'idea', b'Idea'), (b'comment', b'Comment')])),
                ('author', models.ForeignKey(to='app.Author')),
                ('campaign', models.ForeignKey(to='app.Campaign')),
                ('initiative', models.ForeignKey(to='app.Initiative')),
                ('parent_comment', models.ForeignKey(to='app.Comment', null=True)),
                ('parent_idea', models.ForeignKey(to='app.Idea', null=True)),
                ('source_consultation', models.ForeignKey(to='app.ConsultationPlatform', null=True)),
                ('source_social', models.ForeignKey(to='app.SocialNetwork', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='idea',
            name='location',
            field=models.ForeignKey(to='app.Location', null=True),
        ),
        migrations.AddField(
            model_name='idea',
            name='source_consultation',
            field=models.ForeignKey(to='app.ConsultationPlatform', null=True),
        ),
        migrations.AddField(
            model_name='idea',
            name='source_social',
            field=models.ForeignKey(to='app.SocialNetwork', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='location',
            field=models.ForeignKey(to='app.Location', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent_comment',
            field=models.ForeignKey(to='app.Comment', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent_idea',
            field=models.ForeignKey(to='app.Idea', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='source_consultation',
            field=models.ForeignKey(to='app.ConsultationPlatform', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='source_social',
            field=models.ForeignKey(to='app.SocialNetwork', null=True),
        ),
        migrations.AddField(
            model_name='author',
            name='location',
            field=models.ForeignKey(to='app.Location', null=True),
        ),
        migrations.AddField(
            model_name='author',
            name='social_network',
            field=models.ForeignKey(to='app.SocialNetwork', null=True),
        ),
    ]
