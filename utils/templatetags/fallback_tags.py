from django import template
from django.conf import settings
from django.utils import safestring

try:
    from pipeline import conf
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False

register = template.Library()


def _pipeline_shim(type_, pipeline_key, dependency):
    if not HAS_PIPELINE:
        raise ImportError(
            "Please install 'django-pipeline' library to use "
            "fallback_tags."
        )

    shim = None

    fallback_key = None
    debug_fallback_keys = None
    pipeline_dict = settings.PIPELINE[type_].get(pipeline_key)
    if pipeline_dict:
        extra_context = pipeline_dict.get('extra_context')
        if extra_context:
            fallback_key = extra_context.get('fallback_key')
            debug_fallback_keys = extra_context.get('debug_fallback_keys')
    if not conf.settings.PIPELINE_ENABLED and debug_fallback_keys:
        shim = ''
        for value in debug_fallback_keys.values():
            shim += '"{}": "{}",\n'.format(value, dependency)
    elif fallback_key:
        shim = '"{}": "{}",'.format(fallback_key, dependency)
    else:
        raise Exception('Could not shim pipeline with key: ' + pipeline_key)

    return safestring.mark_safe(shim)


@register.simple_tag
def pipeline_js_shim(pipeline_key, dependency):
    return _pipeline_shim('JAVASCRIPT', pipeline_key, dependency)


@register.simple_tag
def pipeline_css_shim(pipeline_key, dependency):
    return _pipeline_shim('STYLESHEETS', pipeline_key, dependency)
