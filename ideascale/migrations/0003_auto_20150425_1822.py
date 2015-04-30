# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0002_auto_20150424_1736'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comment',
            name='parent_id',
        ),
        migrations.AddField(
            model_name='author',
            name='initiative',
            field=models.ForeignKey(default=1, to='ideascale.Initiative'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='campaign',
            name='initiative',
            field=models.ForeignKey(default=1, to='ideascale.Initiative'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='comment',
            name='parent_comment_id',
            field=models.ForeignKey(to='ideascale.Comment', null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='parent_idea_id',
            field=models.ForeignKey(to='ideascale.Idea', null=True),
        ),
        migrations.AddField(
            model_name='initiative',
            name='ideascale_id',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='author',
            name='ideascale_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='ideascale_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='comment',
            name='ideascale_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='idea',
            name='ideascale_id',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='vote',
            name='ideascale_id',
            field=models.PositiveIntegerField(),
        ),
    ]
