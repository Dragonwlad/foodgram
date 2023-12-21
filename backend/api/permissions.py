from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Доступ разрешен только для суперпользователей, администраторов, авторов
    объектов. Остальные пользователи
    могут только просматривать объекты, но не редактировать или удалять их.
    """
    def has_permission(self, request, view):
        return (request.method in SAFE_METHODS
                or request.user.is_staff
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user == obj.author
            or request.user.is_staff
        )
