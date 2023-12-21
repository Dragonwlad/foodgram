from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (DjoserUserViewSet, IngredientViewSet, RecipeViewSet,
                       TagViewSet)

router = DefaultRouter()
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')

router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', DjoserUserViewSet)


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls), ),
]
