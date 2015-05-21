# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20150513_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='external_id',
            field=models.IntegerField(default=-1, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='initiative',
            name='active',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='initiative',
            name='external_id',
            field=models.IntegerField(default=-1, editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='initiative',
            name='name',
            field=models.CharField(max_length=50, editable=False),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='platform',
            field=models.OneToOneField(editable=False, to='app.ConsultationPlatform'),
        ),
        migrations.AlterField(
            model_name='initiative',
            name='url',
            field=models.URLField(editable=False),
        ),
    ]
