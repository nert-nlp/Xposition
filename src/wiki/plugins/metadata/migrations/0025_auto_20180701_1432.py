# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-01 18:32
from __future__ import unicode_literals

from django.db import migrations
import wiki.plugins.metadata.models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0024_auto_20180701_1429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='corpussentence',
            name='word_gloss',
            field=wiki.plugins.metadata.models.SeparatedValuesField(blank=True, max_length=200, verbose_name='Word Gloss'),
        ),
    ]
