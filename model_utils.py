import collections

from django.db import models
from django.core.exceptions import ValidationError


class FieldList():
    Field = collections.namedtuple('Field', ['field', 'value'])

    def get_all_fields(self):
        """Returns a list of all field names on the instance."""

        # use OrderedDict so we can look up values later on
        fields = collections.OrderedDict()
        for f in self._meta.fields:
            fname = f.name
            # resolve picklists/choices, with get_xyz_display() function
            get_choice = 'get_' + fname + '_display'
            if hasattr(self, get_choice):
                value = getattr(self, get_choice)()
            else:
                try:
                    value = getattr(self, fname)
                except:
                    # print("Could not get value of field.")
                    value = None

            if f.editable:
                fields.update({f.name: self.Field(f, value)})

        return fields

    class PseudoField():

        def __init__(self, verbose_name):
            self.verbose_name = verbose_name

    class PseudoForeignKey():

        def __init__(self, verbose_name):
            self.verbose_name = verbose_name


class ImageField(models.ImageField):

    def save_form_data(self, instance, data):
        if data is not None:
            file = getattr(instance, self.attname)
            if file != data:
                file.delete(save=False)
        super(ImageField, self).save_form_data(instance, data)


def _validate_image(field_file):
        file_size = field_file.size
        megabyte_limit = 3.0
        if file_size > megabyte_limit * 1024 * 1024:  # b*kb*mb
            raise ValidationError("Max file size is %sMB"
                                  % str(megabyte_limit))
