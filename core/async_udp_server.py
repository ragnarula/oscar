import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool
from gevent import socket
import socket as _socket


class AsyncUDPServer():
    # state classes first
    class ReadyState():

        def start(self, server):
            server.change_state(AsyncUDPServer.RUNNING_STATE)

        def stop(self, server):
            pass

        def enter(self, server):
            server.sock = server.get_socket()
            server.sock.setblocking(1)

        def exit(self, server):
            pass


    class RunningState():

        def start(self, server):
            pass

        def stop(self, server):
            server.change_state(AsyncUDPServer.READY_STATE)

        def enter(self, server):
            try:
                address = (server.host, server.port)
                server.sock.bind(address)
            except _socket.error:
                server.change_state(AsyncUDPServer.ERROR_STATE)
                return
            server.pool.spawn(server.run)

        def exit(self, server):
            server.sock.close()


    class ErrorState():

        def start(self, server):
            server.change_state(AsyncUDPServer.READY_STATE)
            server.change_state(AsyncUDPServer.RUNNING_STATE)

        def stop(self, server):
            server.change_state(AsyncUDPServer.READY_STATE)

        def enter(self, server):
            pass

        def exit(self, server):
            pass

# server definition stars here
    READY_STATE = ReadyState()
    RUNNING_STATE = RunningState()
    ERROR_STATE = ErrorState()

    def __init__(self, host, port, socket_factory=None, pool=None):
        if pool is None:
            self.pool = Pool()
        else:
            self.pool = pool
        self.msg_handler = None
        self.sock = None
        self.socket_factory = socket_factory
        self.host = host
        self.port = port
        self.state = AsyncUDPServer.READY_STATE
        self.state.enter(self)

    def get_socket(self):
        if self.socket_factory is not None:
            return self.socket_factory()
        return socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)

    def start(self):
        self.state.start(self)

    def stop(self):
        self.state.stop(self)

    def change_state(self, state):
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def run(self):
        while self.state == AsyncUDPServer.RUNNING_STATE:
            try:
                socket.wait_read(self.sock.fileno(), timeout=1)
            except _socket.error:
                continue
            msg = self.sock.recv(4096)
            print "received UDP message " + msg
            if self.msg_handler is not None:
                self.msg_handler(msg)
        print "udp ending"

    def wait(self):
        self.pool.wait()