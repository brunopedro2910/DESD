from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("marketplace", "0003_supplierorderevent")]

    operations = [
        migrations.AddField(
            model_name="supplierorderevent",
            name="note",
            field=models.CharField(blank=True, max_length=240),
        ),
        migrations.AddField(
            model_name="recipe",
            name="products",
            field=models.ManyToManyField(blank=True, related_name="recipes", to="marketplace.product"),
        ),
        migrations.AddConstraint(
            model_name="settlement",
            constraint=models.UniqueConstraint(fields=("producer", "period_start", "period_end"), name="one_settlement_per_producer_period"),
        ),
        migrations.CreateModel(
            name="LoginAudit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("username", models.CharField(max_length=150)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("successful", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
