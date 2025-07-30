from django import template


register = template.Library()


@register.inclusion_tag('utils/snippets/glyphicon.html')
def glyphicon(glyph):
    return {'glyph': glyph}
