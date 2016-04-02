

def as_div(self):
    "Returns this form rendered as HTML <div>s."
    return self._html_output(
        normal_row='<div%(html_class_attr)s>%(label)s %(field)s%(help_text)s</div>',
        error_row='%s',
        row_ender='</div>',
        help_text_html=' <span class="helptext">%s</span>',
        errors_on_separate_row=True)


def as_span(self):
    "Returns this form rendered as HTML <span>s."
    return self._html_output(
        normal_row='<span%(html_class_attr)s>%(label)s %(field)s%(help_text)s</span>',
        error_row='%s',
        row_ender='</span>',
        help_text_html=' <span class="helptext">%s</span>',
        errors_on_separate_row=True)
