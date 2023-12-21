from colorfield.fields import ColorField
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from django.conf import settings

User = get_user_model()


MAX_NAME_LENGTH = 200

MAX_MEASUREMENT_UNIT_LENGTH = 200


class Tag(models.Model):
    """Модель данных для тегов."""
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH,
        unique=True
    )
    color = ColorField('Цветовой код')
    slug = models.SlugField(
        'Slug',
        unique=True
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Ingredient(models.Model):
    """Модель данных для ингредиентов ."""
    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH,
    )
    measurement_unit = models.CharField(
        'Мера',
        max_length=MAX_MEASUREMENT_UNIT_LENGTH,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'], name='unique_ingredient')
        ]

    def __str__(self) -> str:
        return f'{self.name}'


class RecipeCustomQuerySet(models.QuerySet):
    '''Менеджер для создаения доп полей is_favorited и is_in_shopping_cart.'''
    def add_is_in_cart_subquery(self, **kwargs):
        is_in_cart_subquery = Cart.objects.filter(
            user=kwargs.get('user'),
            recipe=models.OuterRef('pk')).values('pk')[:1]
        return self.annotate(
            is_in_shopping_cart=models.Exists(is_in_cart_subquery))

    def add_is_favorite_subquery(self, **kwargs):
        is_favorite_subquery = Favorite.objects.filter(
            user=kwargs.get('user'),
            recipe=models.OuterRef('pk')).values('pk')[:1]

        return self.annotate(is_favorited=models.Exists(is_favorite_subquery))


class Recipe(models.Model):
    """Модель данных для рецептов."""
    objects = RecipeCustomQuerySet.as_manager()

    name = models.CharField(
        'Название',
        max_length=MAX_NAME_LENGTH,
    )
    image = models.ImageField(
        upload_to=settings.IMAGE_DIRECTORY)
    text = models.TextField()
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1),
                    MaxValueValidator(32766)]
    )
    author = models.ForeignKey(
        User, related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        through='RecipeTag',

    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes',
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self) -> str:
        return f'{self.name[:settings.STRING_OUTPUT_LENGTH]}...'


class RecipeTag(models.Model):
    """Связующая модель для рецептов и тегов."""
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'tag'], name='unique_tag')
        ]

    def __str__(self) -> str:
        return f'{self.recipe} tag - {self.tag}'


class RecipeIngredient(models.Model):
    """Связующая модель для рецептов и ингредиентов."""
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipeingredient',
        on_delete=models.PROTECT)
    amount = models.IntegerField(
        'Количество',
        validators=[MinValueValidator(1), ])

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецептов'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient')
        ]

    def __str__(self) -> str:
        return f'{self.recipe} ingredient - {self.ingredient}'


class Favorite(models.Model):
    """Модель данных для добавление рецептов в избранное."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='users_favorits_recipe',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorit_recipe',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'

    def __str__(self) -> str:
        return f'{self.user} added to favorite - {self.recipe}'


class Cart(models.Model):
    """Модель данных для добавление рецептов в корзину."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='carts_user',
        verbose_name='Корзина пользователя',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_in_cart',
        verbose_name='Рецепт в корзине',
    )

    class Meta:
        verbose_name = 'Рецепт в корзине'
        verbose_name_plural = 'Рецепты в корзине'

    def __str__(self) -> str:
        return f'{self.user} added to cart - {self.recipe}'
