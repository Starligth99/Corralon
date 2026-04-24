from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("vehiculos", "0006_perfilusuario_operador_asignado"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="edicion_operador_usada",
            field=models.BooleanField(default=False),
        ),
    ]
