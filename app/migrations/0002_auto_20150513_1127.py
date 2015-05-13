# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Initiatve',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('hashtag', models.CharField(help_text=b"Max length 14 characters (do not include '#')", max_length=14, unique=True, null=True)),
                ('url', models.URLField(default=None, editable=False)),
                ('users', models.IntegerField(default=0, editable=False)),
                ('ideas', models.IntegerField(default=0, editable=False)),
                ('votes', models.IntegerField(default=0, editable=False)),
                ('comments', models.IntegerField(default=0, editable=False)),
            ],
        ),
        migrations.RenameModel(
            old_name='IdeationPlatform',
            new_name='ConsultationPlatform',
        ),
        migrations.RemoveField(
            model_name='ideationcampaign',
            name='ideation_initiative',
        ),
        migrations.RemoveField(
            model_name='ideationinitiatve',
            name='platform',
        ),
        migrations.RemoveField(
            model_name='initiative',
            name='ideation_initiative',
        ),
        migrations.RemoveField(
            model_name='initiative',
            name='social_network',
        ),
        migrations.AlterField(
            model_name='campaign',
            name='hashtag',
            field=models.CharField(help_text=b"Max length 14 characters (do not include '#')", max_length=14, unique=True, null=True),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='initiative',
            field=models.ForeignKey(to='app.Initiatve'),
        ),
        migrations.DeleteModel(
            name='IdeationCampaign',
        ),
        migrations.DeleteModel(
            name='IdeationInitiatve',
        ),
        migrations.DeleteModel(
            name='Initiative',
        ),
        migrations.AddField(
            model_name='initiatve',
            name='platform',
            field=models.OneToOneField(to='app.ConsultationPlatform'),
        ),
        migrations.AddField(
            model_name='initiatve',
            name='social_network',
            field=models.ManyToManyField(to='app.SocialNetwork', blank=True),
        ),
    ]
