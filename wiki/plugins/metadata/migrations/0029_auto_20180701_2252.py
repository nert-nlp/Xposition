# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-07-02 02:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0028_auto_20180701_2234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='construal',
            name='special',
            field=models.CharField(blank=True, default='', max_length=200, null=True),
        ),
    ]