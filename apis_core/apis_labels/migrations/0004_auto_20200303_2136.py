# Generated by Django 2.1.9 on 2020-03-03 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis_labels', '0003_auto_20200303_1547'),
    ]

    operations = [
        migrations.AddField(
            model_name='label',
            name='end_date_is_exact',
            field=models.NullBooleanField(),
        ),
        migrations.AddField(
            model_name='label',
            name='start_date_is_exact',
            field=models.NullBooleanField(),
        ),
    ]