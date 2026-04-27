from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehiculos", "0007_cliente_edicion_operador_usada"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="calle",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="cliente",
            name="colonia",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="cliente",
            name="municipio",
            field=models.CharField(blank=True, max_length=60),
        ),
        migrations.AddField(
            model_name="cliente",
            name="codigo_postal",
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
