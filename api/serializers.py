__author__ = 'raghavnarula'

from api.models import Device
from rest_framework import serializers


class StateField(serializers.Field):

    def to_internal_value(self, data):

        if data not in Device.states_callable:
            raise serializers.ValidationError("Must be one of: "\
                                              + str(Device.states_callable))

        return Device.states.get(data)

    def to_representation(self, obj):
        return Device.states.keys()[Device.states.values().index(obj)]


class DeviceSerializer(serializers.HyperlinkedModelSerializer):
    current_state = serializers.CharField(read_only=True)

    class Meta:
        model = Device
        fields = ('url', 'name', 'host', 'port', 'current_state', 'active', 'timeout')
