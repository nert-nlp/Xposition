# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-06-27 15:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0010_metadata_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='metadata',
            name='template',
            field=models.CharField(default='wiki/view.html', editable=False, max_length=100),
        ),
    ]