# PSL
import os
# 3rd Party
from django.conf import settings


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
