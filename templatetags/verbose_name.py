from django.core import exceptions
from django import template

register = template.Library()


@register.simple_tag
def verbose_field_name(instance, field_name):
    try:
        return instance._meta.get_field(field_name).verbose_name
    except exceptions.FieldDoesNotExist:
        return instance.get_all_fields()[field_name].field.verbose_name
