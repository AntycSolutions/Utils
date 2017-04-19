from django import template
from django.forms import widgets
from django.db import models

from utils import model_utils

register = template.Library()


# form

@register.filter
def get_form_field_type(field):
    return field.field.widget


@register.filter
def is_number(widget):
    return isinstance(widget, widgets.NumberInput)


@register.filter
def is_clearable_file(widget):
    if hasattr(widget, 'widgets'):
        for widget in widget.widgets:
            if isinstance(widget, widgets.ClearableFileInput):
                return True

    return isinstance(widget, widgets.ClearableFileInput)


@register.filter
def is_file(widget):
    if hasattr(widget, 'widgets'):
        for widget in widget.widgets:
            if isinstance(widget, widgets.FileInput):
                return True

    return isinstance(widget, widgets.FileInput)


@register.filter
def is_datetimepicker(widget):
    return isinstance(widget, widgets.DateTimePicker)


@register.filter
def is_date(widget):
    return isinstance(widget, widgets.DateInput)


@register.filter
def is_autocomplete(widget):
    return isinstance(widget, widgets.AutoCompleteSelectWidget)


@register.filter
def is_checkbox(widget):
    return isinstance(widget, widgets.CheckboxInput)


@register.filter
def is_checkboxmultiple(widget):
    return isinstance(widget, widgets.CheckboxSelectMultiple)


# model

@register.filter
def is_image(field):
    return isinstance(field, models.ImageField)


@register.filter
def is_foreignkey(field):
    return isinstance(
        field,
        (
            models.ForeignKey,
            models.OneToOneField,
            model_utils.FieldList.PseudoForeignKey
        )
    )


@register.filter
def is_fileset(field):
    return isinstance(field, model_utils.FieldList.PseudoFileSet)


@register.filter
def is_textfield(field):
    return isinstance(field, models.TextField)


@register.filter
def is_btn(field):
    return isinstance(field, model_utils.FieldList.PseudoBtn)
