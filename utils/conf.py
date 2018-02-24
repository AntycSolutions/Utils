from django.conf import settings as django_settings


utils = 'UTILS'
models = 'MODELS'
base = 'BASE'
generics = 'GENERICS'
versions = 'VERSIONS'

db_per_page_store = 'db_per_page_store'
session_per_page_store = 'session_per_page_store'

settings = {
    models: {
        db_per_page_store: False,
        session_per_page_store: True,
    },
    base: {
        'bootstrap3': False,
        'fallback': False,
        'font_awesome': False,
        'jquery_ui': False,
        'pipeline': False,
    },
    generics: {
        'base_template': 'base.html',
        'date_format': 'M. d, yyyy',
    },
    versions: {
        'fallback_js': '1.1.8',
        'bootstrap_css': '3.3.6',
        'bootstrap_js': '3.3.6',
        'bootstrap-picker_js': '1.7.1',
        'bootstrap-picker_css': '1.7.1',
        'html5shiv_js': '3.7.3',
        'respond_js': '1.4.2',
        'font_awesome_css': '4.6.3',
        'jquery_js': '2.2.4',
        'jquery_ui_css': '1.11.4',
        'jquery_ui_js': '1.11.4',
        'jquery_lazy_js': '1.7.0',
    },
}

django_settings_UTILS = getattr(django_settings, utils, {})

settings[models].update(django_settings_UTILS.get(models, {}))

invalid_pagination_store = (
    settings[models][db_per_page_store] and
    settings[models][session_per_page_store]
)
if invalid_pagination_store:
    raise Exception(
        'Use db_per_page_store or session_per_page_store, not both'
    )

settings[base].update(django_settings_UTILS.get(base, {}))
settings[generics].update(django_settings_UTILS.get(generics, {}))
settings[versions].update(django_settings_UTILS.get(versions, {}))
