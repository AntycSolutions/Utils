import itertools

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.forms import widgets

from utils.forms import widgets as utils_widgets


class MultiFileField(forms.FileField):
    widget = utils_widgets.MultiFileInput
    default_error_messages = {
        'min_num': _(
            'Ensure at least %(min_num)s files are uploaded'
            ' (received %(num_files)s).'
        ),
        'max_num': _(
            'Ensure at most %(max_num)s files are uploaded'
            ' (received %(num_files)s).'
        ),
        'file_size': _(
            'File %(uploaded_file_name)s exceeded'
            ' maximum upload size.'
        ),
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 0)
        self.max_num = kwargs.pop('max_num', None)
        self.maximum_file_size = kwargs.pop('max_file_size', None)

        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            i = super().to_python(item)
            if i:
                ret.append(i)

        return ret

    def validate(self, data):
        super().validate(data)

        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0
        if num_files < self.min_num:
            raise ValidationError(
                self.error_messages['min_num'] % {
                    'min_num': self.min_num, 'num_files': num_files
                }
            )
        elif self.max_num and num_files > self.max_num:
            raise ValidationError(
                self.error_messages['max_num'] % {
                    'max_num': self.max_num, 'num_files': num_files
                }
            )
        for uploaded_file in data:
            has_exceeded_size = (
                self.maximum_file_size and
                uploaded_file.size > self.maximum_file_size
            )
            if has_exceeded_size:
                raise ValidationError(
                    self.error_messages['file_size'] % {
                        'uploaded_file_name': uploaded_file.name
                    }
                )

    def _check_clear(self, data, initial):
        # If the widget got contradictory inputs, we raise a validation error
        if data is widgets.FILE_INPUT_CONTRADICTION:
            raise ValidationError(
                self.error_messages['contradiction'], code='contradiction'
            )
        # False means the field value should be cleared; further validation is
        # not needed.
        if data is False:
            if not self.required:
                return False
            # If the field is required, clearing is not possible (the widget
            # shouldn't return False data in that case anyway). False is not
            # in self.empty_value; if a False value makes it this far
            # it should be validated from here on out as None (so it will be
            # caught by the required check).
            data = None
        if not data and initial:
            return initial

        cleaned_data = super().clean(data)

        return cleaned_data

    def clean(self, data, initial=None):
        cleaned_data = []
        LAST_DATUM = object()
        try:
            both = itertools.zip_longest(data, initial, fillvalue=LAST_DATUM)
        except TypeError:
            # data or initial is not iterable
            checked_data = self._check_clear(data, initial)
            cleaned_data.append(checked_data)
        else:
            for datum, initial_datum in both:
                if initial_datum is not LAST_DATUM:
                    checked_datum = self._check_clear(datum, initial_datum)
                    cleaned_data.append(checked_datum)
                else:
                    cleaned_data.append(datum)

        return cleaned_data

    def bound_data(self, data, initial):
        if isinstance(data, list):
            all_none = True
            for datum in data:
                if datum not in (None, widgets.FILE_INPUT_CONTRADICTION):
                    all_none = False
                    break
            if all_none:
                return initial
        else:
            if data in (None, widgets.FILE_INPUT_CONTRADICTION):
                return initial

        return data
