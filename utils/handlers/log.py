# PSL
from copy import copy
# 3rd Party
from django.utils import log
from django.conf import settings
from django.views import debug
from django.core.cache import cache
# Local
from .. import utils


''' add to settings (this example is for django==2.1)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'utils.handlers.log.AdminEmailLimiterHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
'''


class AdminEmailLimiterHandler(log.AdminEmailHandler):
    def _incr_counter(self, key):
        key = 'error_emails|{}'.format(key)
        counter = cache.incr(key)
        ttl = cache.ttl(key)
        if ttl < 0:
            cache.expire(key, 60 * 5)  # 5 mins
        return counter

    def emit(self, record):
        try:
            request = record.request
            subject = '%s (%s IP): %s' % (
                record.levelname,
                ('internal'
                 if request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS
                 else 'EXTERNAL'),
                record.getMessage()
            )
        except Exception:
            subject = '%s: %s' % (
                record.levelname,
                record.getMessage()
            )
            request = None

        if record.exc_info:
            exc_info = record.exc_info
        else:
            exc_info = (None, record.getMessage(), None)

        reporter = debug.ExceptionReporter(request, is_email=True, *exc_info)

        # generate cache key
        lastframe = reporter.get_traceback_data().get('lastframe', {})
        if lastframe:
            filename = lastframe.get('filename')
            lineno = lastframe.get('lineno')
            key = '{}|{}'.format(filename, lineno)
        else:
            key = str(exc_info)
        try:
            if self._incr_counter(key) > 5:
                return  # email limit hit
        except Exception as e:
            utils.send_sentry(e)

        subject = self.format_subject(subject)

        # Since we add a nicely formatted traceback on our own, create a copy
        # of the log record without the exception data.
        no_exc_record = copy(record)
        no_exc_record.exc_info = None
        no_exc_record.exc_text = None

        message = "%s\n\n%s" % (
            self.format(no_exc_record), reporter.get_traceback_text()
        )
        html_message = (
            reporter.get_traceback_html() if self.include_html else None
        )
        self.send_mail(
            subject, message, fail_silently=True, html_message=html_message
        )
