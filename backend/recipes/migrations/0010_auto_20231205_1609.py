# Generated by Django 3.2.16 on 2023-12-05 13:09

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0009_auto_20231205_1549'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='cooking_time',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(32766)], verbose_name='Время приготовления (в минутах)'),
        ),
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.FloatField(max_length=5, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество'),
        ),
    ]