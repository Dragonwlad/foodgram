from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from recipes.models import Cart, Favorite
from users.models import Follow, User


class UserCartInline(admin.StackedInline):
    model = Cart
    extra = 1
    fk_name = 'user'


class UserFavoriteInline(admin.StackedInline):
    model = Favorite
    extra = 1
    fk_name = 'user'


class FollowedUserInline(admin.StackedInline):
    model = Follow
    extra = 1
    fk_name = 'following'


class FollowingUserInline(admin.StackedInline):
    model = Follow
    extra = 1
    fk_name = 'user'


@admin.register(User)
class UserAdmin(UserAdmin):
    inlines = [FollowedUserInline,
               FollowingUserInline,
               UserCartInline,
               UserFavoriteInline]
    list_display = (
        'username',
        'email',
    )
    search_fields = ('username',)
    list_filter = ('username', 'email')
    empty_value_display = '-empty-'
