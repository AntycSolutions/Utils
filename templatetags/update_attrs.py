# http://vanderwijk.info/blog
# /adding-css-classes-formfields-in-django-templates/

from django import template
register = template.Library()


@register.filter
def update_attrs(field, new_attrs):
    attrs = field.field.widget.attrs

    definition = new_attrs.split('|')
    for d in definition:
        if ':' not in d:
            attrs[d] = True  # support html5 attrs
        else:
            t, v = d.split(':', 1)  # supports style: width: 100px;
            if t in attrs:
                attrs[t] = "{0} {1}".format(attrs[t], v.strip())
            else:
                attrs[t] = v.strip()

    return field.as_widget(attrs=attrs)
