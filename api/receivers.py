__author__ = 'raghavnarula'
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save
from api.models import Device
from core.worker import update_device, delete_device


@receiver(post_save)
def notify(sender,**kwargs):
    pass


@receiver(post_delete, sender=Device)
def notify_delete(sender, instance, **kwargs):
    print "Delete"
    delete_device.delay(instance.name)


@receiver(post_save, sender=Device)
def notify_update(sender, instance, update_fields, **kwargs):
    if update_fields is not None and 'current_state' in update_fields and len(update_fields) is 1:
        return
    print "save"
    update_device.delay(instance.name)

