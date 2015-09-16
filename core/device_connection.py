__author__ = 'raghavnarula'
from async_tcp_client import AsyncTCPClient
from django.db import DatabaseError
import logging


class RemoteDevice:

    def __init__(self, device_model, logger_factory=None, pool=None):
        self.device_model = device_model
        self.connection = AsyncTCPClient(device_model.host, device_model.port,
                                         timeout=device_model.timeout,
                                         logger_factory=logger_factory,
                                         pool=pool,
                                         state_change_listener=self.on_state_change)
        if logger_factory is not None:
            self.logger = logger_factory(__name__)
            self.logger_factory = logger_factory
        else:
            self.logger = logging.getLogger(__name__)
        self.pool = pool
        self.logger.debug("%s Init")

    def on_state_change(self, previous, next):
        self.logger.debug("%s changing state from %s to %s", self.device_model.name, previous.name, next.name)
        if next is AsyncTCPClient.ERROR_STATE and self.device_model.active:
            self.logger.debug("%s entering ERROR_STATE and is active, restarting", self.device_model.name)
            self.connection.stop()
            self.connection = self.get_connection()
            self.connection.start()
        self.device_model.current_state = self.connection.state.name
        try:
            self.device_model.save(update_fields=['current_state'])
            self.logger.debug("%s updated model in DB to state %s",
                              self.device_model.name,
                              self.device_model.current_state)
        except DatabaseError:
            self.logger.debug("%s Caught DatabaseError, failed to update model", self.device_model.name)
            pass

    def start(self):
        self.logger.info("%s Start", self.device_model.name)
        self.connection.start()

    def stop(self):
        self.logger.info("%s Stop", self.device_model.name)
        self.connection.stop()

    def send(self, msg):
        self.logger.info("%s Sending message %s", self.device_model.name, repr(msg))
        self.connection.send(msg)

    def get_connection(self):
        connection = AsyncTCPClient(self.device_model.host, self.device_model.port,
                                    timeout=self.device_model.timeout,
                                    logger_factory=self.logger_factory,
                                    pool=self.pool,
                                    state_change_listener=self.on_state_change)
        return connection

    def update(self):
        self.device_model.refresh_from_db()
        self.logger.debug("%s UPDATING %s:%s tout: %s to %s %s:%s tout: %s act: %s",
                          self.device_model.name, self.connection.host, self.connection.port,
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
            self.connection = self.get_connection()
        if self.device_model.active:
            self.start()
