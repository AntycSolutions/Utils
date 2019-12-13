# PSL
import os
import smtplib
# 3rd Party
from django.conf import settings
from django.core import mail
try:
    import sentry_sdk
except ImportError:
    pass


def get_git_info():
    git_info = os.popen(
        'cd "{}" &&'
        ' git symbolic-ref --short HEAD &&'
        ' git rev-parse HEAD'.format(settings.BASE_DIR)
    ).read().replace('\n', ' ').strip().split(' ')

    if len(git_info) < 2 or not git_info[0] or not git_info[1]:
        return 'Invalid git info', str(git_info)

    branch = git_info[0]
    commit_hash = git_info[1]

    return branch, commit_hash


def send_mail(subject, body, html_message=None, emails=None):
    if not emails:
        emails = list(dict(settings.ADMINS).values())
    try:
        mail.send_mail(
            subject, body, '', emails, html_message=html_message
        )
    except smtplib.SMTPRecipientsRefused as e:
        send_sentry(e)


def send_sentry(e=None, extra=None, tags=None):
    if settings.DEBUG:
        return
    with sentry_sdk.push_scope() as scope:
        if extra:
            for key, val in extra.items():
                scope.set_extra(key, val)
        if tags:
            for key, val in tags.items():
                scope.set_tag(key, val)
        sentry_sdk.capture_exception(e)
