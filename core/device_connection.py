__author__ = 'raghavnarula'
from async_tcp_client import AsyncTCPClient
from django.db import DatabaseError
import logging


class RemoteDevice:

    def __init__(self, device_model, logger_factory=None, pool=None, connection=None):
        self.connection = connection
        self.device_model = device_model

        if logger_factory is not None:
            self.logger = logger_factory(__name__)
            self.logger_factory = logger_factory
        else:
            self.logger = logging.getLogger(__name__)
        self.pool = pool
        self.name = self.device_model.name

    def start(self):
        self.update()
        self.connection.start()

    def stop(self):
        self.connection.stop()

    def send(self, msg):
        self.connection.send(msg)

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
