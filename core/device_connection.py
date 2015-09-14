__author__ = 'raghavnarula'
from async_tcp_client import AsyncTCPClient
from django.db import DatabaseError


class DeviceConnection(AsyncTCPClient):

    class ReadyState(AsyncTCPClient.ReadyState):

        def update(self, conn):
            conn.device.refresh_from_db()
            if conn.device.active:
                conn.start()

        def enter(self, conn):
            AsyncTCPClient.ReadyState.enter(self, conn)
            conn.host = conn.device.host
            conn.port = conn.device.port
            conn.timeout = conn.device.timeout
            conn.active = conn.device.active

    class ConnectingState(AsyncTCPClient.ConnectingState):

        def update(self, conn):
            conn.device.refresh_from_db()
            if conn.device.timeout != conn.timeout:
                conn.timeout = conn.device.timeout
            if (
                conn.device.host != conn.host or
                conn.device.port != conn.port
            ):
                conn.stop()

            if conn.active:
                conn.start()
            else:
                conn.stop()

    class ErrorState(AsyncTCPClient.ErrorState):

        def update(self, conn):
            conn.change_state(AsyncTCPClient.READY_STATE)

        def enter(self, conn):
            AsyncTCPClient.ErrorState.enter(self, conn)
            if conn.active:
                conn.start()

    class TimeoutState(AsyncTCPClient.TimeoutState):

        def update(self, conn):
            conn.change_state(AsyncTCPClient.READY_STATE)

        def enter(self, conn):
            AsyncTCPClient.TimeoutState.enter(self, conn)
            conn.active = False
            conn.device.active = False
            conn.device.save(update_fields=['active'])

    class ConnectedState(AsyncTCPClient.ConnectedState):

        def update(self, conn):
            conn.device.refresh_from_db()
            if conn.device.timeout != conn.timeout:
                conn.timeout = conn.device.timeout
            if (
                conn.device.host != conn.host or
                conn.device.port != conn.port
            ):
                conn.stop()

            if conn.active:
                conn.start()
            else:
                conn.stop()

    AsyncTCPClient.READY_STATE = ReadyState()
    AsyncTCPClient.CONNECTING_STATE = ConnectingState()
    AsyncTCPClient.CONNECTED_STATE = ConnectedState()
    AsyncTCPClient.ERROR_STATE = ErrorState()
    AsyncTCPClient.TIMEOUT_STATE = TimeoutState()

    def __init__(self, device, **kwargs):
        self.device = device
        kwargs['timeout'] = device.timeout
        AsyncTCPClient.__init__(self, device.host, device.port, **kwargs)

    def change_state(self, state):
        print "device " + self.device.name + " changing state from " + self.state.name + " to " + state.name
        AsyncTCPClient.change_state(self, state)
        self.device.current_state = self.state.name
        try:
            self.device.save(update_fields=['current_state'])
        except DatabaseError:
            pass

    def update(self):
        self.state.update(self)
