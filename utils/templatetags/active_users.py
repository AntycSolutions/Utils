from datetime import datetime, timedelta

from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.utils import timezone

from django import template
register = template.Library()


@register.assignment_tag
def get_active_users():
    now = timezone.now()
    sessions = Session.objects.filter(expire_date__gte=now)
    uids = []

    for session in sessions:
        data = session.get_decoded()
        if 'last_logged_in' not in data:
            continue

        last_logged_in_seconds = data['last_logged_in']
        last_logged_in = datetime.fromtimestamp(
            last_logged_in_seconds, tz=now.tzinfo
        )
        # active in the last 10 minutes
        if last_logged_in > (now - timedelta(minutes=10)):
            uids.append(data.get('_auth_user_id', None))

    return User.objects.filter(id__in=uids)
