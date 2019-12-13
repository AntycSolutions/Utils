# PSL
import subprocess
# 3rd Party
from django.core.management import base
# Local
from ... import utils


''' add disk_mon.sh to your project
#!/bin/bash
# as project user:
# chmod +x disk_mon.sh
# add the following to crontab -e
# check diskspace every 10 mins
# */10 * * * * /path/to/disk_mon.sh >> /path/to/disk_mon.log 2>&1
cd /path/to/project
source /virtualenv/bin/activate
python manage.py disk_mon
'''


THRESHOLD = '80'
MAIN_DISK = '/'


class Command(base.BaseCommand):
    help = 'Diskspace monitor'

    def handle(self, *args, **options):
        # assumes an OS with df
        proc = subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE)
        df = proc.stdout.read().decode()
        found = False
        for row in df.split('\n'):
            if not row:
                continue
            cols = row.split()
            if cols[-1] != MAIN_DISK:
                continue
            found = True
            usage = cols[-2][:-1]  # remove %
            if usage >= THRESHOLD:
                utils.send_mail(
                    'Diskspace Low Warning',
                    'Diskspace usage at {}% above threshold {}%'.format(
                        usage, THRESHOLD
                    ),
                )
            break  # gucci
        if not found:
            utils.send_mail(
                'Main Disk Missing',
                'Could not find main disk {}'.format(MAIN_DISK),
            )
