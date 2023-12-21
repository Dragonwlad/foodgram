from django.core.exceptions import ValidationError


def unique_empty_validator(values):
    """Исключение повторения и отсутствия ингредиентов."""
    if not values:
        raise ValidationError(
            {'message': 'You cant create recipe without this field!'}
        )

    values_list = []
    for value in values:
        values_list.append(getattr(value, 'name'))
    values_set = set(values_list)
    if len(values_list) != len(values_set):
        raise ValidationError(
            {'message': 'You cant create recipe with repetitive'
             ' tags or ingredients!'}
        )
