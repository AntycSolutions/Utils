import itertools

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from utils.forms import widgets as utils_widgets


class MultiFileField(forms.FileField):
    # TODO: this doesn't work unless you overide with
    #  ConfirmClearableMultiFileMultiWidget
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
        # data is a list of files
        ret = []
        for item in data:
            if isinstance(item, list):  # last item can be list of new files
                # MultiFileInput
                for new_item in item:
                    i = super().to_python(new_item)
                    # ignore empty_values, no files uploaded
                    if i:
                        ret.append(i)
            else:
                # ConfirmClearableFile
                if item is False:
                    ret.append(item)
                else:
                    i = super().to_python(item)
                    # ignore empty_values, no files uploaded
                    if i:
                        ret.append(i)

        return ret

    def validate(self, data):
        # data is a list of files
        empty = True
        for datum in data:
            # if all are empty or all are False (will be deleted)
            if datum not in self.empty_values + [False]:
                empty = False
                break
        if self.required and empty:
            raise ValidationError(
                self.error_messages['required'], code='required'
            )

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
            if uploaded_file is False:
                continue

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

    def run_validators(self, data):
        # data is a list of files
        for datum in data:
            super().run_validators(data)

    def _check_clear(self, data, initial):
        # data is a file, initial is original file

        # False means the field value should be cleared; further validation is
        #  not needed.
        if data is False:
            # we don't need to check required here as we do it in validate()
            return False

        # form wizard puts temporary files in initial
        #  or the field is required and is returning the file instead of False
        return data

    def clean(self, data, initial=None):
        # data is a list of files, initial is a list of files
        checked_data = []
        LAST_DATUM = object()
        both = itertools.zip_longest(data, initial, fillvalue=LAST_DATUM)
        for datum, initial_datum in both:
            if initial_datum is not LAST_DATUM:
                # ConfirmClearableFile
                checked_datum = self._check_clear(datum, initial_datum)
                checked_data.append(checked_datum)
            else:
                # MultiFileInput
                # datum is a list of new files, doesn't have a clear checkbox
                checked_data.append(datum)

        # we need to skip FileField's clean, so we call its super
        cleaned_data = super(forms.FileField, self).clean(checked_data)

        return cleaned_data

    def bound_data(self, data, initial):
        # data is a list of files, initial is a list of files
        all_none = True
        for datum in data:
            if datum is not None:
                all_none = False
                break
        if all_none:
            return initial

        return data
