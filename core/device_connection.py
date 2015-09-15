__author__ = 'raghavnarula'
from async_tcp_client import AsyncTCPClient
from django.db import DatabaseError
import logging


# class DeviceConnection(AsyncTCPClient):
#
#     class ConnectingState(AsyncTCPClient.ConnectingState):
#
#         def enter(self, conn):
#             AsyncTCPClient.ConnectingState.enter(self, conn)
#
#     class ErrorState(AsyncTCPClient.ErrorState):
#
#         def enter(self, conn):
#             AsyncTCPClient.ErrorState.enter(self, conn)
#             if conn.device.active:
#                 conn.start()
#
#     class TimeoutState(AsyncTCPClient.TimeoutState):
#
#         def enter(self, conn):
#             AsyncTCPClient.TimeoutState.enter(self, conn)
#             conn.device.active = False
#             conn.device.save(update_fields=['active'])
#
#     AsyncTCPClient.CONNECTING_STATE = ConnectingState()
#     AsyncTCPClient.ERROR_STATE = ErrorState()
#     AsyncTCPClient.TIMEOUT_STATE = TimeoutState()
#
#     def __init__(self, device, **kwargs):
#         self.device = device
#         kwargs['timeout'] = device.timeout
#         AsyncTCPClient.__init__(self, device.host, device.port, **kwargs)
#
#     def change_state(self, state):
#         AsyncTCPClient.change_state(self, state)
#         self.device.current_state = self.state.name
#         try:
#             self.device.save(update_fields=['current_state'])
#         except DatabaseError:
#             pass
#
#     def update(self):
#         self.device.refresh_from_db()
#         self.logger.debug("Updating %s:%s tout: %s to %s:%s tout: %s act: %s",
#                           self.host, self.port, self.timeout,
#                           self.device.host, self.device.port, self.device.timeout, self.device.active)
#         if not self.device.active:
#             self.stop()
#
#         if self.device.timeout != self.timeout:
#             self.timeout = self.device.timeout
#         if (
#             self.device.host != self.host or
#             self.device.port != self.port
#         ):
#             self.stop()
#             self.host = self.device.host
#             self.port = self.device.port
#
#         if self.device.active:
#             self.start()


class RemoteDevice:

    def __init__(self, device_model, logger_factory=None, pool=None):
        self.device_model = device_model
        self.connection = AsyncTCPClient(device_model.host, device_model.port,
                                         timeout=device_model.timeout,
                                         logger_factory=logger_factory,
                                         pool=pool)
        if logger_factory is not None:
            self.logger = logger_factory(__name__)
            self.logger_factory = logger_factory
        else:
            self.logger = logging.getLogger(__name__)
        self.pool = pool
        self.name = self.device_model.name

    def start(self):
        self.connection.start()

    def stop(self):
        self.connection.stop()

    def update(self):
        self.device_model.refresh_from_db()
        self.logger.debug("%s UPDATING %s:%s tout: %s to %s %s:%s tout: %s act: %s",
                          self.name, self.connection.host, self.connection.port,
                          self.connection.timeout, self.device_model.name,
                          self.device_model.host, self.device_model.port,
                          self.device_model.timeout, self.device_model.active)

        if not self.device_model.active:
            self.stop()

        if self.device_model.timeout != self.connection.timeout:
            self.connection.timeout = self.device_model.timeout
        if (
            self.device_model.host != self.connection.host or
            self.device_model.port != self.connection.port
        ):
            self.stop()
            self.connection = AsyncTCPClient(self.device_model.host, self.device_model.port,
                                             timeout=self.device_model.timeout,
                                             logger_factory=self.logger_factory,
                                             pool=self.pool)
        if self.device_model.active:
            self.start()
