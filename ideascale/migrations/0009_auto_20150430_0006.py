# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ideascale', '0008_auto_20150429_2247'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vote',
            name='idea',
        ),
        migrations.AddField(
            model_name='vote',
            name='parent_comment',
            field=models.ForeignKey(to='ideascale.Comment', null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='parent_idea',
            field=models.ForeignKey(to='ideascale.Idea', null=True),
        ),
        migrations.AddField(
            model_name='vote',
            name='parent_type',
            field=models.CharField(default='idea', max_length=50),
            preserve_default=False,
        ),
    ]
