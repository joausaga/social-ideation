# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20150513_1127'),
    ]

    operations = [
        migrations.CreateModel(
            name='Initiative',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('hashtag', models.CharField(help_text=b"Max length 14 characters (do not include '#')", max_length=14, unique=True, null=True)),
                ('url', models.URLField(default=None, editable=False)),
                ('users', models.IntegerField(default=0, editable=False)),
                ('ideas', models.IntegerField(default=0, editable=False)),
                ('votes', models.IntegerField(default=0, editable=False)),
                ('comments', models.IntegerField(default=0, editable=False)),
                ('platform', models.OneToOneField(to='app.ConsultationPlatform')),
                ('social_network', models.ManyToManyField(to='app.SocialNetwork', blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='initiatve',
            name='platform',
        ),
        migrations.RemoveField(
            model_name='initiatve',
            name='social_network',
        ),
        migrations.AlterField(
            model_name='campaign',
            name='initiative',
            field=models.ForeignKey(to='app.Initiative'),
        ),
        migrations.DeleteModel(
            name='Initiatve',
        ),
    ]
