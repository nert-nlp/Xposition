# Generated by Django 3.1 on 2021-03-04 14:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0046_corpus_deprecated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ptokenannotation',
            name='is_abbr',
            field=models.BooleanField(default=False, verbose_name='Abbrev?'),
        ),
    ]