# Generated by Django 2.1.2 on 2019-06-14 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('apis_metainfo', '0001_initial'),
        ('apis_labels', '0001_initial'),
        ('apis_vocabularies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='label',
            name='label_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apis_vocabularies.LabelType'),
        ),
        migrations.AddField(
            model_name='label',
            name='temp_entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apis_metainfo.TempEntityClass'),
        ),
    ]