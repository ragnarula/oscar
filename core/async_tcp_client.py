import gevent
import gevent.monkey
gevent.monkey.patch_all()
from gevent.pool import Pool
from gevent.queue import Queue
from gevent import socket
import socket as _socket
import logging

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

    def __init__(self, host, port, socket_factory=None, pool=None, timeout=None, logger_factory=None):
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
        if logger_factory is None:
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = logger_factory(__name__)

    def get_socket(self):
        if self.socket_factory is not None:
            return self.socket_factory()
        return socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)

    def start(self):
        self.logger.info("Starting %s", self.host)
        self.state.start(self)

    def stop(self):
        self.logger.info("Stopping %s", self.host)
        self.state.stop(self)

    def send(self, msg):
        self.logger.info("Sending to %s", self.host)
        self.state.send(self, msg)

    def change_state(self, state):
        self.logger.info("Connection to %s changing state from %s to %s", self.host, self.state.name, state.name)
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def connect_loop(self):
        connection_attempts = 0
        while self.state == AsyncTCPClient.CONNECTING_STATE:
            if self.timeout is not None and connection_attempts > self.timeout:
                self.sock.close()
                self.change_state(AsyncTCPClient.TIMEOUT_STATE)
                self.logger.debug("Connection to %s exceeded timeout of %s", self.host, self.timeout)
                break
            connection_attempts += 1
            try:
                self.logger.debug("Attepmpting to connect to %s on port %s", self.host, self.port)
                address = (self.host, int(self.port))
                self.sock.connect(address)
            except _socket.error:
                self.sock.close()
                self.sock = self.get_socket()
                self.logger.debug("Could not connect to %s on port %s, waiting 1 to try again",
                                  self.host,
                                  self.port)
                gevent.sleep(1)
                continue
            self.logger.debug("Connection to %s on port %s established", self.host, self.port)
            self.msg_queue = Queue()
            self.change_state(AsyncTCPClient.CONNECTED_STATE)
            self.logger.debug("Spawning thread for receive loop")
            self.pool.spawn(self.receive_loop)
            self.logger.debug("Spawning thread for send loop")
            self.pool.spawn(self.send_loop)

    def receive_loop(self):
        while self.state == AsyncTCPClient.CONNECTED_STATE:
            try:
                socket.wait_read(self.sock.fileno(), timeout=1)
            except _socket.error:
                continue
            msg = self.get_line()
            self.logger.debug("Received %s from %s on port %s", repr(msg), self.host, self.port)
            if self.msg_handler is not None and msg is not None:
                self.msg_handler(msg)

    def get_line(self):
        data = []
        while self.state == AsyncTCPClient.CONNECTED_STATE:
            try:
                msg = self.sock.recv(4096)
            except _socket.error:
                self.change_state(AsyncTCPClient.ERROR_STATE)
                break
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
            self.logger.debug("Sending message %s to %s on port %s", repr(msg), self.host, self.port)
            try:
                socket.wait_write(self.sock.fileno(), timeout=1)
                self.sock.sendall(str(msg))
            except _socket.error:
                self.logger.debug("Unable to send message %s to %s on port $s", repr(msg), self.host, self.port)
                continue
            self.logger.debug("Sent message %s to %s on port %s", repr(msg), self.host, self.port)

    def wait(self):
        self.pool.wait()
