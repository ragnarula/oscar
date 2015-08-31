from __future__ import absolute_import
from celery import shared_task
__author__ = 'raghavnarula'

@shared_task
def run_server():
    pass


@shared_task
def update_device(device):
    pass


@shared_task
def delete_device(device):
    pass

