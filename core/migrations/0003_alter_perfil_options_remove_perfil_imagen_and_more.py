# Generated by Django 5.0.14 on 2025-04-19 22:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_detalleboleta_bodega_remove_boleta_cliente_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='perfil',
            options={'ordering': ['usuario__username'], 'verbose_name': 'Perfil de usuario', 'verbose_name_plural': 'Perfiles de usuarios'},
        ),
        migrations.RemoveField(
            model_name='perfil',
            name='imagen',
        ),
        migrations.RemoveField(
            model_name='perfil',
            name='subscrito',
        ),
        migrations.RemoveField(
            model_name='perfil',
            name='tipo_usuario',
        ),
    ]
