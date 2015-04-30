# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0005_auto_20150428_1350'),
    ]

    operations = [
        migrations.CreateModel(
            name='URLParameter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('description', models.CharField(max_length=150, null=True, blank=True)),
                ('type', models.CharField(max_length=50, choices=[(b'str', b'String'), (b'num', b'Number'), (b'bool', b'Boolean')])),
                ('required', models.BooleanField(default=True)),
            ],
        ),
        migrations.RenameField(
            model_name='callback',
            old_name='params',
            new_name='body_params',
        ),
        migrations.AddField(
            model_name='callback',
            name='url_params',
            field=models.ManyToManyField(to='connectors.URLParameter', blank=True),
        ),
    ]
