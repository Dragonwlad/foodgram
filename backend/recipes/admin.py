from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, RecipeTag, Tag

admin.site.empty_value_display = '-empty'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'color'
    )
    search_fields = ('name',)
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'measurement_unit'
    )
    search_fields = ('name',)
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeTagInline(admin.StackedInline):
    model = RecipeTag
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    readonly_fields = ('favorites_count',)
    inlines = [RecipeIngredientInline, RecipeTagInline]
    list_display = (
        'name',
        'author',
    )
    search_fields = ('name',)
    list_filter = ('author', 'name', 'tags')
    fields = ('author',
              'name',
              'image',
              'text',
              'cooking_time',
              'favorites_count')

    @admin.display(description='Добавили в избранное:')
    def favorites_count(self, obj):
        return obj.favorit_recipe.all().count()
