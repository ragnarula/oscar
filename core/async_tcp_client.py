import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue
from gevent import socket
import socket as _socket


class AsyncTCPClient:
    # state classes first
    class ReadyState:
        name = 'READY'

        def start(self, client):
            client.change_state(AsyncTCPClient.CONNECTING_STATE)

        def stop(self, client):
            pass

        def send(self, client, msg):
            pass

        def enter(self, client):
            client.sock = client.get_socket()
            client.sock.setblocking(1)
            client.msg_queue = Queue()

        def exit(self, client):
            pass

    class ConnectingState:
        name = 'CONNECTING'

        def start(self, client):
            pass

        def stop(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)

        def send(self, client, msg):
            pass

        def enter(self, client):
            client.pool.spawn(client.connect_loop)

        def exit(self, client):
            pass

    class ConnectedState:
        name = 'CONNECTED'

        def start(self, client):
            pass

        def stop(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)

        def send(self, client, msg):
            client.msg_queue.put(msg)

        def enter(self, client):
            pass

        def exit(self, client):
            client.sock.close()

    class ErrorState:
        name = 'ERROR'

        def start(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)
            client.change_state(AsyncTCPClient.CONNECTING_STATE)

        def stop(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)

        def send(self, server, msg):
            pass

        def enter(self, server):
            pass

        def exit(self, server):
            pass

    class TimeoutState:
        name = 'TIMEOUT'

        def start(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)
            client.change_state(AsyncTCPClient.CONNECTING_STATE)

        def stop(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)

        def send(self, server, msg):
            pass

        def enter(self, server):
            pass

        def exit(self, server):
            pass

# server definition stars here

    READY_STATE = ReadyState()
    CONNECTING_STATE = ConnectingState()
    CONNECTED_STATE = ConnectedState()
    ERROR_STATE = ErrorState()
    TIMEOUT_STATE = TimeoutState()

    def __init__(self, host, port, socket_factory=None, pool=None, timeout=None):
        if pool is None:
            self.pool = Pool()
        else:
            self.pool = pool
        self.timeout = timeout
        self.msg_handler = None
        self.sock = None
        self.socket_factory = socket_factory
        self.host = host
        self.port = port
        self.msg_queue = None
        self.state = AsyncTCPClient.READY_STATE
        self.state.enter(self)

    def get_socket(self):
        if self.socket_factory is not None:
            return self.socket_factory()
        return socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)

    def start(self):
        self.state.start(self)

    def stop(self):
        self.state.stop(self)

    def send(self, msg):
        self.state.send(self, msg)

    def change_state(self, state):
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def connect_loop(self):
        connection_attempts = 0
        while self.state == AsyncTCPClient.CONNECTING_STATE:
            if self.timeout is not None and connection_attempts > self.timeout:
                self.sock.close()
                self.change_state(AsyncTCPClient.TIMEOUT_STATE)
                break
            connection_attempts += 1
            try:
                address = (self.host, int(self.port))
                self.sock.connect(address)
            except _socket.error:
                self.sock.close()
                self.sock = self.get_socket()
                gevent.sleep(1)
                continue
            self.msg_queue = Queue()
            self.change_state(AsyncTCPClient.CONNECTED_STATE)
            self.pool.spawn(self.receive_loop)
            self.pool.spawn(self.send_loop)

    def receive_loop(self):
        while self.state == AsyncTCPClient.CONNECTED_STATE:
            try:
                socket.wait_read(self.sock.fileno(), timeout=1)
            except _socket.error:
                continue
            msg = self.get_line()
            if self.msg_handler is not None and msg is not None:
                self.msg_handler(msg)

    def get_line(self):
        data = []
        while self.state == AsyncTCPClient.CONNECTED_STATE:
            msg = self.sock.recv(4096)
            if msg is None or len(msg) == 0:
                self.change_state(AsyncTCPClient.ERROR_STATE)
                break
            data.append(msg)
            if msg.endswith('\n'):
                break
        if len(data) > 0:
            return ''.join(data)

    def send_loop(self):
        while self.state == AsyncTCPClient.CONNECTED_STATE:
            try:
                msg = self.msg_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue
            try:
                socket.wait_write(self.sock.fileno(), timeout=1)
                self.sock.sendall(str(msg))
            except _socket.error:
                continue

    def wait(self):
        self.pool.wait()
