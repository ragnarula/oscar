__author__ = 'raghavnarula'
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from api.models import Device
# from oscar.celeryapp import app
import zerorpc

@receiver(post_save)
def notify(sender,**kwargs):
    pass


# @receiver(post_delete, sender=Device)
# def notify_delete(instance, **kwargs):
#     print "Delete"
#     app.send_task('core.worker.control_task', args=["DEL", instance.name], kwargs={}, queue="core")
#
#
# @receiver(post_save, sender=Device)
# def notify_update(instance, update_fields, **kwargs):
#     if update_fields is not None and 'current_state' in update_fields and len(update_fields) is 1:
#         return
#     print "save"
#     app.send_task('core.worker.control_task', args=["UP", instance.name], kwargs={}, queue="core")


@receiver(post_delete, sender=Device)
def notify_delete(instance, **kwargs):
    print "Delete"
    c = zerorpc.Client()
    c.connect("ipc://oscars")
    c.delete(instance.name)


@receiver(post_save, sender=Device)
def notify_update(instance, update_fields, **kwargs):
    if update_fields is not None and 'current_state' in update_fields and len(update_fields) is 1:
        return
    print "save"
    c = zerorpc.Client()
    c.connect("ipc://oscars")
    c.update(instance.name)

