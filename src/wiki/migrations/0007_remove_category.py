
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0006_auto_20190819_0056'),
    ]

    operations = [
        migrations.DeleteModel(name='articlecategory'),
        migrations.DeleteModel(name='categoryrelation')
    ]
