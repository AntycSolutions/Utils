from django import template
from django.utils import safestring

register = template.Library()


@register.filter()
def get_attr(obj, attr):
    return getattr(obj, attr)
