# Generated by Django 5.0.14 on 2025-05-11 05:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_rename_codigo_pregunta_codi'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pregunta',
            old_name='codi',
            new_name='codigo',
        ),
    ]
