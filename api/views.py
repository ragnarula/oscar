from django.shortcuts import render
from rest_framework import viewsets
from api.models import Device
from api.serializers import DeviceSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
