# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2017-05-03 08:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0018_influence_efn'),
    ]

    operations = [
        migrations.AddField(
            model_name='price',
            name='url',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
