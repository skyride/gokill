# Generated by Django 2.1.1 on 2018-10-02 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20181001_2226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='killmail',
            name='position_x',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='killmail',
            name='position_y',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='killmail',
            name='position_z',
            field=models.FloatField(default=None, null=True),
        ),
    ]