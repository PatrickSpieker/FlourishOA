# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-13 17:38
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_auto_20160713_0215'),
    ]

    operations = [
        migrations.RenameField(
            model_name='price',
            old_name='journal_issn',
            new_name='journal',
        ),
        migrations.RenameField(
            model_name='publisher',
            old_name='journal_issn',
            new_name='journal',
        ),
        migrations.RenameField(
            model_name='publisher',
            old_name='publisher',
            new_name='publisher_name',
        ),
    ]