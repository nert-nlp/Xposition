# Generated by Django 3.1.14 on 2022-08-30 14:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('metadata', '0049_parallelptokenalignment'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='corpussentence',
            name='is_parallel',
        ),
    ]
