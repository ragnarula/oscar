from django.db import models


# Create your models here.
class Device(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    host = models.CharField(max_length=30)
    port = models.CharField(max_length=5)
    active = models.BooleanField(default=False)
    current_state = models.CharField(max_length=10, default="READY")
    timeout = models.IntegerField(default=None, null=True, blank=True)
