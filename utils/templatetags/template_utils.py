import importlib

from django import template

register = template.Library()


@register.filter()
def get_attr(obj, attr):
    return getattr(obj, attr)


@register.assignment_tag
def get_app_settings(app_name):
    app = importlib.import_module(app_name + '.settings')

    return app
