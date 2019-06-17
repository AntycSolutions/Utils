import importlib

from django import template


register = template.Library()
if not hasattr(register, 'assignment_tag'):
    register.assignment_tag = register.simple_tag


@register.filter()
def get_attr(obj, attr):
    return getattr(obj, attr)


@register.filter
def get_item(dict_, key):
    return dict_[key]


@register.assignment_tag
def get_app_settings(app_name):
    try:
        app = importlib.import_module(app_name + '.settings')
    except ImportError:
        app = importlib.import_module(app_name + '.conf')

    return app
