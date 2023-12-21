from django.contrib.auth.models import AbstractUser
from django.db import models

MAX_FIO_LENGTH = 150
MAX_EMAIL_LENGTH = 254


class User(AbstractUser):
    """Класс пользователей."""
    email = models.EmailField(
        verbose_name='email address',
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
    )
    first_name = models.CharField(
        'Имя',
        blank=False,
        null=False,
        max_length=MAX_FIO_LENGTH,
    )
    last_name = models.CharField(
        'Фамилия',
        blank=False,
        null=False,
        max_length=MAX_FIO_LENGTH,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Класс подписок пользователей."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Кто подписался',
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='На кого подписался',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_follow'),
            models.CheckConstraint(check=~models.Q(user=models.F('following')),
                                   name='prevent_self_follow', )
        ]

    def __str__(self):
        return f'{ self.user } subscribed to { self.following }'
