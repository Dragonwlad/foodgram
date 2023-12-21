from django_filters.rest_framework import FilterSet, filters

from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(FilterSet):

    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all()
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_recipe_in_shopping_cart',
    )
    is_favorited = filters.BooleanFilter(
        method='filter_recipe_in_favorite',
    )

    class Meta:
        model = Recipe
        fields = ('name', 'tags', 'author', 'is_in_shopping_cart',
                  'is_favorited')

    def filter_recipe_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(recipe_in_cart__user=user)

        return queryset

    def filter_recipe_in_favorite(self, queryset, name, value):
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorit_recipe__user=user)

        return queryset


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name', lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ('name', )
