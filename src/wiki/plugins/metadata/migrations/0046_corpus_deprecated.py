# Generated by Django 2.2.13 on 2020-08-09 04:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0045_auto_20191203_1144'),
    ]

    operations = [
        migrations.AddField(
            model_name='corpus',
            name='deprecated',
            field=models.BooleanField(default=False, verbose_name='Is this a deprecated version of a corpus?'),
        ),
    ]
