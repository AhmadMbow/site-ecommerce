from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('boutique', '0024_alter_adresse_options_alter_panieritem_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='adresse',
            name='latitude',
            field=models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Latitude GPS du client'),
        ),
        migrations.AddField(
            model_name='adresse',
            name='longitude',
            field=models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True, help_text='Longitude GPS du client'),
        ),
    ]
