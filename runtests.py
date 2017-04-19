import os
import sys

import django
from django.conf import settings
from django.test import utils


def runtests():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.test_settings'
    django.setup()

    TestRunner = utils.get_runner(settings)
    test_runner = TestRunner()
    cases = (len(sys.argv) > 1 and sys.argv[1]) or "tests"
    print('\nRunning test cases: {}\n'.format(cases))
    test_runner.run_tests([cases])


if __name__ == '__main__':
    runtests()
