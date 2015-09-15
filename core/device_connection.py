__author__ = 'raghavnarula'
from async_tcp_client import AsyncTCPClient
from django.db import DatabaseError


class DeviceConnection(AsyncTCPClient):

    class ConnectingState(AsyncTCPClient.ConnectingState):

        def enter(self, conn):
            AsyncTCPClient.ConnectingState.enter(self, conn)

    class ErrorState(AsyncTCPClient.ErrorState):

        def enter(self, conn):
            AsyncTCPClient.ErrorState.enter(self, conn)
            if conn.device.active:
                conn.start()

    class TimeoutState(AsyncTCPClient.TimeoutState):

        def enter(self, conn):
            AsyncTCPClient.TimeoutState.enter(self, conn)
            conn.device.active = False
            conn.device.save(update_fields=['active'])

    AsyncTCPClient.CONNECTING_STATE = ConnectingState()
    AsyncTCPClient.ERROR_STATE = ErrorState()
    AsyncTCPClient.TIMEOUT_STATE = TimeoutState()

    def __init__(self, device, **kwargs):
        self.device = device
        kwargs['timeout'] = device.timeout
        AsyncTCPClient.__init__(self, device.host, device.port, **kwargs)

    def change_state(self, state):
        AsyncTCPClient.change_state(self, state)
        self.device.current_state = self.state.name
        try:
            self.device.save(update_fields=['current_state'])
        except DatabaseError:
            pass

    def update(self):
        self.device.refresh_from_db()
        if not self.device.active:
            self.stop()

        if self.device.timeout != self.timeout:
            self.timeout = self.device.timeout
        if (
            self.device.host != self.host or
            self.device.port != self.port
        ):
            self.stop()
            self.host = self.device.host
            self.port = self.device.port

        if self.device.active:
            self.start()
