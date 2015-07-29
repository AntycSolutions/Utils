from django import template
register = template.Library()


@register.filter
def get_form_field_type(field):
    return field.field.widget.__class__.__name__


@register.filter
def is_number(type):
    return type in ["NumberInput"]


@register.filter
def is_file(type):
    return type in ["ClearableFileInput"]


@register.filter
def is_datetimepicker(type):
    return type in ["DateTimePicker"]


@register.filter
def is_date(type):
    return type in ["DateInput"]


@register.filter
def is_autocomplete(type):
    return type in ["AutoCompleteSelectWidget"]


@register.filter
def get_model_field_type(field):
    return field.__class__.__name__


@register.filter
def is_image(type):
    return type in ["ImageField"]


@register.filter
def is_foreignkey(type):
    return type in ["ForeignKey", "PseudoForeignKey"]
