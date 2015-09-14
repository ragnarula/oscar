__author__ = 'raghavnarula'
from django.db import DatabaseError
import gevent
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue
from async_tcp_client import AsyncTCPClient
from api.models import Device


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

            if conn.device.active:
                conn.start()
            else:
                conn.stop()

    class ErrorState(AsyncTCPClient.ErrorState):

        def update(self, conn):
            conn.change_state(AsyncTCPClient.READY_STATE)

        def enter(self, conn):
            AsyncTCPClient.ErrorState.enter(self, conn)
            if conn.device.active:
                conn.start()

    class TimeoutState(AsyncTCPClient.TimeoutState):

        def update(self, conn):
            conn.change_state(AsyncTCPClient.READY_STATE)

        def enter(self, conn):
            AsyncTCPClient.TimeoutState.enter(self, conn)
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

            if conn.device.active:
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


class ConnectionManager:

    class ReadyState:

        def start(self, manager):
            manager.change_state(ConnectionManager.RUNNING_STATE)

        def stop(self, manager):
            pass

        def enter(self, manager):
            pass

        def exit(self, manager):
            pass

        def send_osc_message(self, manager, message):
            pass

    class RunningState:
        def start(self, manager):
            pass

        def stop(self, manager):
            manager.change_state(ConnectionManager.READY_STATE)

        def enter(self, manager):
            manager.osc_msg_queue = Queue()
            devices = Device.objects.all()
            for d in devices:
                conn = DeviceConnection(d, pool=manager.pool)
                conn.change_state(DeviceConnection.READY_STATE)
                if d.active:
                    conn.start()
                gevent.sleep()
                manager.connection_map[d.name] = conn
            manager.pool.spawn(manager.run_loop)

        def exit(self, manager):
            for c in manager.connection_map.values():
                c.stop()

        def send_osc_message(self, manager, msg):
            manager.osc_msg_queue.put(msg)

    READY_STATE = ReadyState()
    RUNNING_STATE = RunningState()

    def __init__(self, pool=None, logger_factory=None):
        if pool is None:
            self.pool = Pool()
        else:
            self.pool = pool
        self.logger_factory = logger_factory
        self.osc_msg_queue = None
        self.connection_map = {}
        self.state = ConnectionManager.READY_STATE
        self.state.enter(self)

    def change_state(self, state):
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def start(self):
        self.state.start(self)

    def stop(self):
        self.state.stop(self)

    def send_osc_message(self, msg):
        self.state.send_osc_message(self, msg)

    def run_loop(self):
        while self.state == ConnectionManager.RUNNING_STATE:
            try:
                osc_msg = self.osc_msg_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue
            if osc_msg is None is None:
                continue
            try:
                name = osc_msg.path_list.pop()
                action = osc_msg.path_list.pop()
            except IndexError:
                return
            if action == "message":
                try:
                    connection = self.connection_map[name]
                except KeyError:
                    return
                for p in osc_msg.params:
                    connection.send(p)
        print "manager ending"

    def update(self, name):
        try:
            conn = self.connection_map[name]
        except KeyError:
            self.add_device(name)
            return
        conn.update()
        print "updated device " + conn.device.name

    def delete(self, name):
        try:
            conn = self.connection_map[name]
        except KeyError:
            return
        conn.stop()
        del self.connection_map[name]
        print "removed device " + conn.device.name

    def add_device(self, name):
        try:
            device = Device.objects.get(pk=name)
        except Device.DoesNotExist:
            return
        conn = DeviceConnection(device, pool=self.pool, logger_factory=self.logger_factory)
        if device.active:
            conn.start()
        self.connection_map[device.name] = conn
        print "added device " + conn.device.name
