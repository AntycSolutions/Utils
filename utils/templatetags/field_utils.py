from django import template
from django.forms import widgets

register = template.Library()


@register.filter
def get_form_field_type(field):
    return field.field.widget


@register.filter
def is_number(type):
    return isinstance(type, widgets.NumberInput)


@register.filter
def is_file(type):
    if hasattr(type, 'widgets'):
        for widget in type.widgets:
            if isinstance(widget, widgets.ClearableFileInput):
                return True

    return isinstance(type, widgets.ClearableFileInput)


@register.filter
def is_datetimepicker(type):
    return isinstance(type, widgets.DateTimePicker)


@register.filter
def is_date(type):
    return isinstance(type, widgets.DateInput)


@register.filter
def is_autocomplete(type):
    return isinstance(type, widgets.AutoCompleteSelectWidget)


@register.filter
def is_checkbox(type):
    return isinstance(type, widgets.CheckboxInput)


@register.filter
def get_model_field_type(field):
    return field.__class__.__name__


@register.filter
def is_image(type):
    return type in ["ImageField"]


@register.filter
def is_foreignkey(type):
    return type in ["ForeignKey", "PseudoForeignKey"]


@register.filter
def is_fileset(type):
    return type in ["PseudoFileSet"]


@register.filter
def is_textfield(type):
    return type in ["TextField"]
