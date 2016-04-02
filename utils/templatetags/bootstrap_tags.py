from django import template
from django.utils import safestring
from django.utils import html

register = template.Library()


@register.filter()
def bootstrap_tags(tags):
    bootstrap_alerts = ['debug', 'info', 'success', 'warning']
    output = ""
    for tag in tags.split():
        if tag in bootstrap_alerts:
            tag_output = ' alert-{0}'.format(tag)
        elif tag == 'error':  # django error == bootstrap danger
            tag_output = ' alert-danger'
        else:
            tag_output = ' {0}'.format(html.conditional_escape(tag))

        output += tag_output

    return safestring.mark_safe(output)
