# Generated by Django 4.2.13 on 2024-10-24 01:16

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ficha_tecnica', '0001_initial'),
        ('almacen', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('codigo_producto', models.CharField(blank=True, max_length=20, null=True, verbose_name='Código del producto')),
                ('nombre_comercial', models.CharField(max_length=255, verbose_name='Nombre comercial')),
                ('product_final', models.BooleanField(default=True, verbose_name='Producto final')),
                ('cantidad_alm', models.IntegerField(default=0, verbose_name='Cantidad almacenada')),
                ('ficha_costo', models.FileField(null=True, upload_to='', verbose_name='Ficha de costo')),
                ('almacen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='almacen.almacen', verbose_name='Almacen')),
                ('ficha_tecnica_folio', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='ficha_tecnica.fichatecnica', verbose_name='Ficha técnica folio')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]