from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool
import zerorpc
import os
from django.conf import settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oscar.settings")
from core.async_udp_server import AsyncUDPServer
from core.osc_message_parser import OSCMessageParser
from core.connection_manager import ConnectionManager


class Core:

    def __init__(self, pool):
        self.pool = pool
        self.udp_server = AsyncUDPServer('', 6060, pool=self.pool)
        self.osc_message_parser = OSCMessageParser(pool=self.pool)
        self.connection_manager = ConnectionManager(pool=self.pool)
        self.udp_server.msg_handler = self.osc_message_parser.add_message
        self.osc_message_parser.device_msg_handler = self.connection_manager.send_osc_message

    def start(self):
        self.osc_message_parser.start()
        self.udp_server.start()
        self.connection_manager.start()

    def stop(self):
        self.udp_server.stop()
        self.osc_message_parser.stop()
        self.connection_manager.stop()

    def update(self, device):
        self.connection_manager.update(device)

    def delete(self, device):
        self.connection_manager.delete(device)


def main():

    pool = Pool()
    s = zerorpc.Server(Core(pool))
    print "binding"
    s.bind("ipc://oscars")
    print "running"
    s.run()
    pool.join()

if __name__ == "__main__":
    main()
