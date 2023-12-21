# Generated by Django 3.2.16 on 2023-12-02 10:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_auto_20231202_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.FloatField(max_length=5, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество'),
        ),
    ]
