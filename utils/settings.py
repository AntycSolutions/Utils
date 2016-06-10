from django.conf import settings

VERSIONS = {
    'fallback_js': '1.1.8',
    'bootstrap_css': '3.3.6',
    'bootstrap_js': '3.3.6',
    'html5shiv_js': '3.7.3',
    'respond_js': '1.4.2',
    'font_awesome_css': '4.6.3',
    'jquery_js': '2.2.4',
    'jquery_ui_css': '1.11.4',
    'jquery_ui_js': '1.11.4',
    'jquery_lazy_js': '1.7.0',
}
VERSIONS.update(getattr(settings, 'VERSIONS', {}))
