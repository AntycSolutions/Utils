import json

from django.db import models
from django.conf import settings


class Paginate(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )

    raw_rows_per_page = models.TextField(blank=True)

    @property
    def rows_per_page_json(self):
        if not self.raw_rows_per_page:
            return {}

        return json.loads(self.raw_rows_per_page)

    @rows_per_page_json.setter
    def rows_per_page_json(self, obj):
        self.raw_rows_per_page = json.dumps(obj)
