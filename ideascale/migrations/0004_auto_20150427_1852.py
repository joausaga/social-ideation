# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ideascale', '0003_auto_20150425_1822'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='TestingParameters',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=10, choices=[(b'int', b'Integer'), (b'str', b'String'), (b'bool', b'Boolean')])),
            ],
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='parent_comment_id',
            new_name='parent_comment',
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='parent_idea_id',
            new_name='parent_idea',
        ),
        migrations.RemoveField(
            model_name='initiative',
            name='ideascale_id',
        ),
        migrations.RemoveField(
            model_name='initiative',
            name='token',
        ),
        migrations.AddField(
            model_name='comment',
            name='sync',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='idea',
            name='sync',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='vote',
            name='sync',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='author',
            name='ideascale_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='ideascale_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='ideascale_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='ideascale_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='location',
            field=models.ForeignKey(to='ideascale.Location', null=True),
        ),
        migrations.AlterField(
            model_name='idea',
            name='positive_votes',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AlterField(
            model_name='vote',
            name='ideascale_id',
            field=models.PositiveIntegerField(unique=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_comment',
            field=models.ForeignKey(related_name='+', to='ideascale.Comment', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_comment_idea',
            field=models.ForeignKey(related_name='+', to='ideascale.Comment', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_idea',
            field=models.ForeignKey(related_name='+', to='ideascale.Idea', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_vote',
            field=models.ForeignKey(related_name='+', to='ideascale.Vote', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_vote_comment',
            field=models.ForeignKey(related_name='+', to='ideascale.Vote', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='last_vote_idea',
            field=models.ForeignKey(related_name='+', to='ideascale.Vote', null=True),
        ),
        migrations.AddField(
            model_name='client',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
    ]
