import base64

from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserSerializer
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserListSerializer(UserSerializer):
    """Сериализатор отображения пользователей."""
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and Follow.objects.filter(user=request.user,
                                          following=obj).exists())


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug', )


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit', )


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор сокращенного отображения рецептов."""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class IngredientShowSerializer(serializers.ModelSerializer):
    """Сериализатор отображения ингредиентов с количеством в рецептах."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id',
                  'name',
                  'measurement_unit',
                  'amount')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор отображения рецептов."""
    tags = TagSerializer(many=True)
    ingredients = IngredientShowSerializer(
        many=True, source='recipe_ingredients', read_only=True,)
    author = UserListSerializer()
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор сохранения ингредиентов в рецептах."""
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', )


class RecipeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=True,
    )
    image = Base64ImageField(required=True, allow_null=False)
    ingredients = RecipeIngredientCreateSerializer(many=True, required=True)

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def to_representation(self, instance):
        """Функция для передачи request в context, для получения данных
        о пользователе в сериализаторах."""
        serializer = RecipeSerializer(
            instance,
            context={'request': self.context.get('request')})
        return serializer.data

    def create_update_recipe(self, ingredients_data, recipe):
        """Функция для сохранения/обновления вложенных полей рецепта."""
        recipe_ingredients = []
        for ingredient_data in ingredients_data:
            recipe_ingredients.append(RecipeIngredient(recipe=recipe,
                                                       **ingredient_data))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    @transaction.atomic
    def create(self, validated_data):
        """Функция для сохранения вложенных полей."""
        user = self.context['request'].user
        validated_data['author'] = user
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.create_update_recipe(ingredients_data, recipe)
        return recipe

    @transaction.atomic
    def update(self, validated_data, instance):
        """Функция для обновления вложенных полей."""
        ingredients_data = instance.pop('ingredients')
        validated_data.ingredients.clear()
        validated_data.tags.clear()
        self.create_update_recipe(ingredients_data, validated_data)
        return super().update(validated_data, instance)

    def validate(self, attrs):
        if not attrs.get('ingredients'):
            raise serializers.ValidationError(
                {'message': 'You cant create recipe without ingredients!'})
        values_list = []
        for value in attrs['ingredients']:
            values_list.append(value['ingredient'].id)
        values_set = set(values_list)
        if len(values_list) != len(values_set):
            raise serializers.ValidationError(
                {'message': 'You cant create recipe'
                 ' wiht repetitive ingredients!'})
        if not attrs.get('tags'):
            raise serializers.ValidationError(
                {'message': 'You cant create recipe without tags!'})
        values_set = set(attrs['tags'])
        if len(attrs['tags']) != len(values_set):
            raise serializers.ValidationError(
                {'message': 'You cant create recipe'
                 ' wiht repetitive tags!'})
        return attrs


class SubscriptionsSerializer(UserListSerializer):
    '''Сериализатор просмотра подписок.'''
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',
                  )

    def get_recipes(self, obj):
        recipes = obj.recipes.all()
        recipes_limit = self.context['request'].query_params.get(
            'recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
            return RecipeShortSerializer(recipes, many=True).data

        return RecipeShortSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SubscribeSerializer(serializers.ModelSerializer):
    '''Сериализатор создания/удаления подписок.'''
    class Meta:
        model = Follow
        fields = ('user',
                  'following',)
        validators = [
            UniqueTogetherValidator(
                queryset=Follow.objects.all(),
                fields=('user', 'following'),
                message='Подписка уже существует.'
            )
        ]

    def validate_following(self, following):
        if self.context['request'].user == following:
            raise serializers.ValidationError(
                'You cant follow yourself!')
        return following

    def to_representation(self, instance):
        serializer = SubscriptionsSerializer(
            instance.following, context={
                'request': self.context.get('request')})
        return serializer.data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор записи/удаления рецептов в избранном."""

    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в избранном.'
            )]

    def to_representation(self, instance):
        serializer = RecipeShortSerializer(instance.recipe)
        return serializer.data


class ShopingCardSerializer(FavoriteSerializer):
    """Сериализатор записи/удаления рецептов в корзине."""

    class Meta:
        model = Cart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Cart.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже в корзине.')
        ]
