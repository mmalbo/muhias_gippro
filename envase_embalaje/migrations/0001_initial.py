# Generated by Django 4.2.13 on 2024-10-24 01:16

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('tipo_envase_embalaje', '0001_initial'),
        ('almacen', '0001_initial'),
        ('formato', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvaseEmbalaje',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('codigo_envase', models.CharField(max_length=20, unique=True, verbose_name='Código del envase')),
                ('estado', models.CharField(choices=[('comprado', 'Comprado'), ('en_almacen', 'En almacén'), ('reservado', 'Reservado')], max_length=255, verbose_name='Estado')),
                ('cantidad', models.IntegerField(default=0, null=True, verbose_name='Cantidad en almacen')),
                ('almacen', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='almacen.almacen', verbose_name='Almacen')),
                ('formato', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='formato.formato', verbose_name='Formato de envase')),
                ('tipo_envase_embalaje', models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='tipo_envase_embalaje.tipoenvaseembalaje', verbose_name='Tipo de envase de embalaje')),
            ],
            options={
                'verbose_name': 'Envase o embalaje',
                'verbose_name_plural': 'Envases o embalajes',
            },
        ),
    ]
