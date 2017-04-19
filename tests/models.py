# required to run tests

from os import path

from django.db import models
from django.conf import settings


class File(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    file = models.FileField(upload_to='tests/')

    def filename(self):
        if self.file:
            return path.basename(self.file.name)

    def __str__(self):
        return '{}'.format(self.filename())
