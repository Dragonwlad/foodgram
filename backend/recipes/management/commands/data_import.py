import csv
from io import open

from django.core.management.base import BaseCommand

from django.conf import settings
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Import ingredients to DB'

    def handle(self, *args, **options):

        with open(settings.BASE_DIR / 'recipes/data/ingredients.csv',
                  encoding='utf-8') as f:
            reader = csv.DictReader(f)
            ingredients = []
            for row in reader:
                ingredients.append(Ingredient(
                    name=row['name'],
                    measurement_unit=row['measurement_unit']))
            try:
                Ingredient.objects.bulk_create(ingredients,
                                               ignore_conflicts=True)
            except ImportError:
                print('Что-то пошло не так')
        print('Данные импортированы!')
