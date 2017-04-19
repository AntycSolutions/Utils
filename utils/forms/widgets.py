from django.core.files import uploadedfile
from django.forms import widgets
from django.utils.html import conditional_escape
from django.utils import safestring


# supports multiple file upload on one widget
class MultiFileInput(widgets.FileInput):
    def render(self, name, value, attrs=None):
        attrs['multiple'] = 'multiple'

        return super().render(name, value, attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):  # MultiValueDict
            value = files.getlist(name)
        else:  # dict
            value = files.get(name)

        # list of files or None
        return value


# renders only the file and clear checkbox (removes file upload input)
#  used with ConfirmClearableFile/ConfirmClearableMultiFileMultiWidget
#  could be used with ClearableMultiFileMultiWidget (needs creating)
class ClearableFile(widgets.ClearableFileInput):
    def value_from_datadict(self, data, files, widget_name):
        upload = files.get(widget_name)

        value = self._check_clear(upload, data, files, widget_name)

        if value is None:
            if hasattr(self, 'field_name'):
                # widget_name should have format <field_name>_<#>
                index = int(widget_name[-1:])
                # form wizard puts temporary files in initial
                value = self.form.initial[self.field_name][index]

        return value

    def _check_clear(self, upload, data, files, name):
        is_checked = widgets.CheckboxInput().value_from_datadict(
            data, files, self.clear_checkbox_name(name)
        )
        if is_checked:
            # we don't need to check required here as we do it in
            #  MultiFileField.validate()
            # False signals to clear any existing value, as opposed to just
            #  None
            return False

        return upload

    def render(self, widget_name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
        }

        # don't display browse for files button
        template = 'EMPTY<br />'

        if self.is_initial(value) or value is False:
            checked = False

            if value is False:
                # value False means the checkbox is checked, pass True
                checked = True

                # we assume we're in a ConfirmClearableMultiFileMultiWidget
                #  and have self.field_name
                # widget_name should have format <field_name>_<#>
                widget_index = int(widget_name[-1:])
                field_file = (
                    self.form.initial[self.field_name][widget_index]
                )

                value = field_file

            if isinstance(value, uploadedfile.UploadedFile):
                # form wizard files can be temporarily uploaded between steps
                substitutions['initial_text'] = 'Pending'

            # don't display change and browse for files button
            template = (
                '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
                '%(clear_template)s<br />'
            )
            # set initial/initial_url
            substitutions.update(self.get_template_substitution_values(value))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(widget_name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = \
                    conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = \
                    conditional_escape(checkbox_id)
                substitutions['clear'] = widgets.CheckboxInput().render(
                    checkbox_name, checked, attrs={'id': checkbox_id}
                )
                substitutions['clear_template'] = \
                    self.template_with_clear % substitutions

        output = safestring.mark_safe(template % substitutions)

        return output


class MissingFormIdException(Exception):
    pass


class MissingFormInstanceException(Exception):
    pass


# add confirmation to clearing files via js
class ConfirmClearableFileBase:
    script = '''
        <script type="text/javascript">
            document.getElementById("%(form_id)s").addEventListener(
                "submit", function(event) {
                    var clear = document.getElementById("%(clear_id)s");
                    if (clear.checked) {
                        var c = confirm(
                            "Are you sure you want to clear %(file_name)s?"
                        );
                        if (!c) { event.preventDefault(); }
                    }
                }
            );
        </script>
    '''

    def __init__(self, *args, **kwargs):
        if 'form_id' not in kwargs:
            raise MissingFormIdException(
                '{} requires the form id.'.format(self.__class__.__name__)
            )
        if 'form' not in kwargs:
            raise MissingFormInstanceException(
                '{} requires the form instance.'.format(
                    self.__class__.__name__
                )
            )
        if 'field_name' in kwargs:
            self.field_name = kwargs.pop('field_name')

        self.form_id = kwargs.pop('form_id')
        self.form = kwargs.pop('form')

        super().__init__(*args, **kwargs)

    def render(self, widget_name, value, attrs=None):
        html = super().render(widget_name, value, attrs)

        if hasattr(self, 'field_name'):
            # ConfirmClearableFile/ConfirmClearableMultiFileMultiWidget
            field_name = self.field_name
            # widget_name should have format <field_name>_<#>
            widget_index = int(widget_name[-1:])
            file_name = self.form.initial[field_name][widget_index]
        else:
            # ConfirmClearableFileInput
            file_name = self.form.initial[widget_name]

        if file_name:
            html += self.script % {
                'clear_id': '{0}-clear_id'.format(widget_name),
                'form_id': self.form_id,
                'file_name': file_name
            }
        # else:  # empty file field

        return safestring.mark_safe(html)


# add confirmation to ClearableFileInput (usually used with FileField)
class ConfirmClearableFileInput(
    ConfirmClearableFileBase, widgets.ClearableFileInput
):
    pass


# add confirmation to ClearableFile
#  used in ConfirmClearableMultiFileMultiWidget/MultiFileField
class ConfirmClearableFile(
    ConfirmClearableFileBase, ClearableFile
):
    pass


# a MultiWidget where each existing file is a ConfirmClearableFile and
#  new files are handled by MultiFileInput
#  used with MultiFileField
class ConfirmClearableMultiFileMultiWidget(widgets.MultiWidget):
    def __init__(self, form_id, form, field_name, file_count, attrs=None):
        widgets = []
        for i in range(file_count):
            widgets.append(
                ConfirmClearableFile(
                    form_id=form_id, form=form, field_name=field_name
                )
            )

        widgets.append(MultiFileInput())

        super().__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        output = "Current Number of Files: {0}<br />".format(
            len(rendered_widgets) - 1  # Last widget is the MultiFileInput
        )
        # ignore last widget as it is the MultiFileInput
        confirm_multi_file_widgets = rendered_widgets[:-1]
        for i, rendered_widget in enumerate(confirm_multi_file_widgets):
            output += "{0}. {1}".format(
                i + 1,  # humans like 1 based arrays
                rendered_widget
            )

        output += rendered_widgets[-1]  # MultiFileInput

        return output

    def decompress(self, value):
        if not value:
            # if no data and initial is not a list
            return [None for widget in self.widgets]
