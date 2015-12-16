from django.core import exceptions
from django import template
from django.template import defaultfilters

register = template.Library()


@register.simple_tag
def verbose_field_name(instance, field_name):
    try:
        verbose_field_name = defaultfilters.capfirst(
            instance._meta.get_field(field_name).verbose_name
        )
    except exceptions.FieldDoesNotExist:
        verbose_field_name = defaultfilters.capfirst(
            instance.get_all_fields()[field_name].field.verbose_name
        )

    return verbose_field_name
