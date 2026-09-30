from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(max_length=20, unique=True, verbose_name="código")),
                ("name", models.CharField(max_length=120, verbose_name="nombre")),
                ("category", models.CharField(choices=[("computadoras", "Computadoras"), ("monitores", "Monitores"), ("perifericos", "Periféricos"), ("componentes", "Componentes"), ("otros", "Otros")], max_length=20, verbose_name="categoría")),
                ("description", models.TextField(blank=True, verbose_name="descripción")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(0)], verbose_name="precio")),
                ("stock", models.PositiveIntegerField(default=0, verbose_name="stock")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="creado")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="actualizado")),
            ],
            options={"ordering": ["name"]},
        ),
    ]
