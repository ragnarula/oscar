__author__ = 'raghavnarula'
from django.apps import AppConfig


class APIConfig(AppConfig):
    name = 'api'
    verbose_name = 'Oscar Device API'

    def ready(self):
        import api.receivers