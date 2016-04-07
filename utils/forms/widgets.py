from django.forms import widgets
from django.utils.html import conditional_escape
from django.utils import safestring


class MultiFileInput(widgets.ClearableFileInput):

    def render(self, name, value, attrs=None):
        attrs['multiple'] = 'multiple'
        return super().render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            value_list = files.getlist(name)
        else:
            value = files.get(name)
            if isinstance(value, list):
                value_list = value
            elif value is None:
                value_list = None
            else:
                value_list = [value]

        if value_list:
            return_list = []
            for upload in value_list:
                return_list.append(self._check_clear(upload, data, files,
                                                     name))
        else:
            return_list = self._check_clear(None, data, files, name)

        return return_list

    def _check_clear(self, upload, data, files, name):
        is_checked = widgets.CheckboxInput().value_from_datadict(
            data, files, self.clear_checkbox_name(name)
        )
        if not self.is_required and is_checked:
            if upload:
                # If the user contradicts themselves (uploads a new file AND
                # checks the "clear" checkbox), we return a unique marker
                # object that FileField will turn into a ValidationError.
                return widgets.FILE_INPUT_CONTRADICTION
            # False signals to clear any existing value, as opposed to just
            #  None
            return False

        return upload


class ClearableFile(widgets.ClearableFileInput):

    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }

        # don't display browse for files button
        template = 'EMPTY<br />'

        if self.is_initial(value):
            # don't display change and browse for files button
            template = (
                '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
                '%(clear_template)s<br />'
            )
            substitutions.update(self.get_template_substitution_values(value))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = \
                    conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = \
                    conditional_escape(checkbox_id)
                substitutions['clear'] = widgets.CheckboxInput().render(
                    checkbox_name, False, attrs={'id': checkbox_id}
                )
                substitutions['clear_template'] = \
                    self.template_with_clear % substitutions

        output = safestring.mark_safe(template % substitutions)

        return output


class ConfirmFileWidgetBase():
    script = '''
        <script>
            document.getElementById("%(form_id)s").addEventListener(
                "submit", function(event) {
                    var clear = document.getElementById("%(clear_id)s");
                    if (clear.checked) {
                        var c = confirm("Are you sure you want to clear"
                                        + " %(file_name)s?");
                        if (!c) { event.preventDefault(); }
                    }
                }
            );
        </script>
    '''

    def __init__(self, *args, **kwargs):
        if 'form_id' not in kwargs:
            raise Exception('ConfirmFileWidget requires the form id.')
        if 'form' not in kwargs:
            raise Exception('ConfirmFileWidget requires the form instance.')
        if 'field_name' in kwargs:
            self.field_name = kwargs.pop('field_name')

        self.form_id = kwargs.pop('form_id')
        self.form = kwargs.pop('form')

        super().__init__(*args, **kwargs)

    def render(self, name, value, attrs=None):
        html = super().render(name, value, attrs)

        if hasattr(self, 'field_name'):
            field_name = self.field_name
            widget_index = int(name[-1:])
            file_name = self.form.initial[field_name][widget_index]
        else:
            field_name = name
            file_name = self.form.initial[field_name]

        widget_name = name

        if field_name in self.form.initial and self.form.initial[field_name]:
            html += self.script % {
                'clear_id': '{0}-clear_id'.format(widget_name),
                'form_id': self.form_id,
                'file_name': file_name
            }
        # else:  # empty file field

        return safestring.mark_safe(html)


class ConfirmFileWidget(ConfirmFileWidgetBase, widgets.ClearableFileInput):
    pass


class ConfirmMultiFileWidget(ConfirmFileWidgetBase, ClearableFile,
                             MultiFileInput):
    pass


class ConfirmMultiFileMultiWidget(widgets.MultiWidget):

    def __init__(self, form_id, form, field_name, file_count, attrs=None):
        widgets = []
        for i in range(file_count):
            widgets.append(ConfirmMultiFileWidget(form_id=form_id, form=form,
                                                  field_name=field_name))

        widgets.append(MultiFileInput())

        super().__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        output = "Current Number of Files: {0}<br />".format(
            len(rendered_widgets) - 1  # Last widget is the multiupload
        )
        for i, rendered_widget in enumerate(rendered_widgets[:-1]):  # no last
            output += "{0}. {1}".format(i + 1,  # humans like 1 based arrays
                                        rendered_widget)
        else:
            output += rendered_widgets[-1]  # last

        return output

    def decompress(self, value):
        if not value:
            return [None for widget in self.widgets]

        return value
