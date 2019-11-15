# Generated by Django 2.1.2 on 2019-06-14 10:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0009_alter_user_last_name_max_length'),
        ('apis_metainfo', '0001_initial'),
        ('apis_vocabularies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='text',
            name='kind',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apis_vocabularies.TextType'),
        ),
        migrations.AddField(
            model_name='text',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apis_metainfo.Source'),
        ),
        migrations.AddField(
            model_name='tempentityclass',
            name='collection',
            field=models.ManyToManyField(to='apis_metainfo.Collection'),
        ),
        migrations.AddField(
            model_name='tempentityclass',
            name='source',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apis_metainfo.Source'),
        ),
        migrations.AddField(
            model_name='tempentityclass',
            name='text',
            field=models.ManyToManyField(blank=True, to='apis_metainfo.Text'),
        ),
        migrations.AddField(
            model_name='collection',
            name='collection_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apis_vocabularies.CollectionType'),
        ),
        migrations.AddField(
            model_name='collection',
            name='groups_allowed',
            field=models.ManyToManyField(to='auth.Group'),
        ),
        migrations.AddField(
            model_name='collection',
            name='parent_class',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='apis_metainfo.Collection'),
        ),
    ]
