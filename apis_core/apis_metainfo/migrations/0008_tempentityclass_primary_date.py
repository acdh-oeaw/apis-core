# Generated by Django 2.1.9 on 2020-08-19 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apis_metainfo', '0007_remove_text_lang'),
    ]

    operations = [
        migrations.AddField(
            model_name='tempentityclass',
            name='primary_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
