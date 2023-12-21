from collections import defaultdict

import xlwt
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from rest_framework import filters, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import CustomPagination
from api.permissions import IsOwnerOrAdminOrReadOnly
from api.serializers import (FavoriteSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             ShopingCardSerializer, SubscribeSerializer,
                             SubscriptionsSerializer, TagSerializer)
from recipes.models import (Cart, Favorite, Ingredient, Recipe,
                            RecipeIngredient, Tag, User)
from users.models import Follow


class DjoserUserViewSet(views.UserViewSet):
    """Всюсет пользователей."""
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action == 'me':
            self.permission_classes = [IsAuthenticated]

        return super().get_permissions()

    @action(["get", ], detail=False,
            permission_classes=[IsAuthenticated],
            serializer_class=SubscriptionsSerializer)
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        queryset = self.paginate_queryset(queryset)
        serializer = SubscriptionsSerializer(queryset, many=True,
                                             context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id):
        current_user = request.user
        if self.request.method == 'POST':
            serializer = SubscribeSerializer(
                data={'user': current_user.id,
                      'following': id}, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        following_user = get_object_or_404(User, id=id)
        subscription = Follow.objects.filter(user=current_user,
                                             following=following_user)
        deleted = subscription.delete()[0]
        if not deleted:
            raise serializers.ValidationError(
                {"error": "You are not following this user!"})
        return Response(
            {'message': 'You have successfully unsubsribed!'},
            status=status.HTTP_204_NO_CONTENT)


class TagIngredientSubscriptionsMixin(viewsets.ReadOnlyModelViewSet):
    """Базовый класс для тегов, ингредиентов и подписок"""
    permission_classes = (AllowAny,)


class TagViewSet(TagIngredientSubscriptionsMixin):
    """Вьюсет для просмотра тегов"""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(TagIngredientSubscriptionsMixin):
    """Вьюсет для объектов модели ингредиентов."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filterset_class = IngredientFilter
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для создания/редактирования и просмотра рецептов."""
    queryset = Recipe.objects.all()
    serializer_class = RecipeCreateSerializer
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, )
    filterset_class = RecipeFilter
    search_fields = ('^name', )
    http_method_names = ('get', 'post', 'patch', 'delete', )
    permission_classes = (IsOwnerOrAdminOrReadOnly, )
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer

        return RecipeSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Recipe.objects.all().select_related(
            'author').prefetch_related('tags').prefetch_related(
                Prefetch('recipe_ingredients',
                         queryset=RecipeIngredient.objects.select_related(
                             'ingredient')))
        if not user.is_authenticated:
            return queryset

        queryset = queryset.add_is_in_cart_subquery(
            user=user).add_is_favorite_subquery(user=user)
        return queryset

    def _add_recipe_to_user(self, request, pk, Serializer):
        serializer = Serializer(
            data={'user': request.user.id, 'recipe': pk},
            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _remove_recipe_from_user(self, request, pk, Model, obj):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite_recipe = Model.objects.filter(user=request.user,
                                               recipe=recipe)
        deleted = favorite_recipe.delete()[0]
        if not deleted:
            raise serializers.ValidationError(
                {'error': f'This recipe is not in {obj}!'})
        return Response(
            {'message': f'You have successfully deleted recipe from {obj}!'},
            status=status.HTTP_204_NO_CONTENT)

    @action(['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk, *args):
        if self.request.method == 'POST':
            return self._add_recipe_to_user(request, pk, FavoriteSerializer)

        return self._remove_recipe_from_user(request, pk, Favorite,
                                             obj='favorite')

    @action(['post', 'delete'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk, *args):
        if self.request.method == 'POST':
            return self._add_recipe_to_user(request, pk, ShopingCardSerializer)

        return self._remove_recipe_from_user(request, pk, Cart,
                                             obj='shopping cart')

    @action(['get', ], detail=False,
            permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        user_cart = Recipe.objects.filter(recipe_in_cart__user=user)
        shopping_ingredients = defaultdict(int)
        for recipe in user_cart:
            for ingredient in recipe.recipe_ingredients.all():
                shopping_ingredients[
                    f'{ingredient.ingredient},'
                    f'{ingredient.ingredient.measurement_unit}'
                ] += ingredient.amount
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Список продуктов')
        row_num = 0
        for key, value in shopping_ingredients.items():
            ws.write(row_num, 0, key)
            ws.write(row_num, 1, value)
            row_num += 1
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = (
            'attachment; filename="list_ingredients.xls"')
        wb.save(response)
        return response
