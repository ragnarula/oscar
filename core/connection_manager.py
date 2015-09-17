__author__ = 'raghavnarula'

import gevent
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue
from api.models import Device
from device_connection import RemoteDevice

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
                conn = RemoteDevice(d, pool=manager.pool, logger_factory=manager.logger_factory)
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
        self.logger = logger_factory(__name__)
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
        gevent.sleep(1)
        try:
            conn = self.connection_map[name]
        except KeyError:
            self.logger.error("Device not found, adding", exc_info=True)
            self.add_device(name)
            return
        self.logger.info("%s Updating", name)
        conn.update()

    def delete(self, name):
        try:
            conn = self.connection_map[name]
        except KeyError:
            self.logger.error("Cant delete device, does not exist", exc_info=True)
            return
        self.logger.info("%s Deleting", name)
        conn.stop()
        del self.connection_map[name]

    def add_device(self, name):
        try:
            device = Device.objects.get(pk=name)
        except Device.DoesNotExist, e:
            self.logger.error("Could not add device", exc_info=True)
            return
        self.logger.info("%s Adding", name)
        conn = RemoteDevice(device, pool=self.pool, logger_factory=self.logger_factory)
        if device.active:
            self.logger.info("%s Starting", name)
            conn.start()
        self.connection_map[device.name] = conn
