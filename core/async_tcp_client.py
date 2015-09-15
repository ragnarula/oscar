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
            client.msg_queue = Queue()

        def exit(self, client):
            pass

    class ConnectingState:
        name = 'CONNECTING'

        def start(self, client):
            pass

        def stop(self, client):
            client.change_state(AsyncTCPClient.DISCONNECTING_STATE)

        def send(self, client, msg):
            pass

        def enter(self, client):
            client.logger.debug("Spawning connection loop for %s:%s", client.host, client.port)
            client.pool.spawn(client.connect_loop)

        def exit(self, client):
            pass

    class ConnectedState:
        name = 'CONNECTED'

        def start(self, client):
            pass

        def stop(self, client):
            client.change_state(AsyncTCPClient.DISCONNECTING_STATE)

        def send(self, client, msg):
            client.msg_queue.put(msg)

        def enter(self, client):
            pass

        def exit(self, client):
            client.sock.close()

    class DisconnectingState:
        name = 'DISCONNECTING'

        def start(self, client):
            pass

        def stop(self, client):
            pass

        def send(self, client, msg):
            pass

        def enter(self, client):
            client.sock.close()
            client.change_state(AsyncTCPClient.READY_STATE)

        def exit(self, client):
            pass

    class ErrorState:
        name = 'ERROR'

        def start(self, client):
            client.change_state(AsyncTCPClient.READY_STATE)
            client.change_state(AsyncTCPClient.CONNECTING_STATE)

        def stop(self, client):
            pass

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
            pass

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
    DISCONNECTING_STATE = DisconnectingState()
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
        sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_KEEPALIVE, 1)
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_KEEPINTVL, 1)
        sock.setsockopt(_socket.IPPROTO_TCP, _socket.TCP_KEEPCNT, 5)
        sock.setblocking(0)
        sock.settimeout(1)
        return sock

    def start(self):
        self.logger.info("Starting %s:%s", self.host, self.port)
        self.state.start(self)

    def stop(self):
        self.logger.info("Stopping %s:%s", self.host, self.port)
        self.state.stop(self)

    def send(self, msg):
        self.logger.info("Sending to %s:%s", self.host, self.port)
        self.state.send(self, msg)

    def change_state(self, state):
        self.logger.info("Connection %s:%s changing state from %s to %s",
                         self.host,
                         self.port,
                         self.state.name,
                         state.name)
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def connecting(self):
        return self.state == AsyncTCPClient.CONNECTING_STATE

    def connect_loop(self):
        connection_attempts = 0
        while self.connecting():
            if self.timeout is not None and connection_attempts > self.timeout:
                self.sock.close()
                self.change_state(AsyncTCPClient.TIMEOUT_STATE)
                self.logger.debug("Connection to %s:%s exceeded timeout of %s",
                                  self.host,
                                  self.port,
                                  self.timeout)
                break
            connection_attempts += 1
            try:
                self.logger.debug("Attepmpting to connect to %s:%s", self.host, self.port)
                address = (self.host, int(self.port))
                self.sock.connect(address)
            except _socket.error:
                self.sock.close()
                self.logger.debug("Could not connect to %s:%s, waiting 1 to try again",
                                  self.host,
                                  self.port)
                gevent.sleep(1)
                if self.connecting():
                    self.sock = self.get_socket()
                    continue
                break
            self.logger.debug("Connection to %s:%s established", self.host, self.port)
            self.msg_queue = Queue()
            self.change_state(AsyncTCPClient.CONNECTED_STATE)
            self.logger.debug("Spawning thread for receive loop")
            self.pool.spawn(self.receive_loop)
            self.logger.debug("Spawning thread for send loop")
            self.pool.spawn(self.send_loop)
        self.logger.debug("Connection loop ending for %s:%s", self.host, self.port)

    def connected(self):
        return self.state == AsyncTCPClient.CONNECTED_STATE

    def receive_loop(self):
        while self.connected():
            msg = self.get_line()
            if self.msg_handler is not None and msg is not None:
                self.logger.debug("Received %s from %s:%s", repr(msg), self.host, self.port)
                self.msg_handler(msg)
        self.logger.debug("%s:%s receive loop ending", self.host, self.port)

    def get_line(self):
        data = []
        while self.connected():
            msg = ''
            try:
                msg = self.sock.recv(4096)
            except _socket.timeout:
                print "timeout"
                continue
            except _socket.error:
                if self.connected():
                    self.logger.debug("Socket error on connection to %s:%s, changing to ERROR_STATE",
                                      self.host,
                                      self.port)
                    self.change_state(AsyncTCPClient.ERROR_STATE)
                    break
            if msg == '':
                if self.connected():
                    self.logger.debug("Empty msg on connection to %s:%s, changing to ERROR_STATE",
                                      self.host,
                                      self.port)
                    self.change_state(AsyncTCPClient.ERROR_STATE)
                    break
            data.append(msg)
            if msg.endswith('\n'):
                break
        if len(data) > 0:
            return ''.join(data)

    def send_loop(self):
        while self.connected():
            try:
                msg = self.msg_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue
            self.logger.debug("Sending message %s to %s:%s", repr(msg), self.host, self.port)
            try:
                socket.wait_write(self.sock.fileno(), timeout=1)
                self.sock.sendall(str(msg))
            except _socket.timeout:
                continue
            except _socket.error:
                self.logger.debug("Unable to send message %s:%s on port $s", repr(msg), self.host, self.port)
                self.change_state(AsyncTCPClient.ERROR_STATE)
                break
            self.logger.debug("Sent message %s to %s:%s", repr(msg), self.host, self.port)
        self.logger.debug("%s:%s send loop ending", self.host, self.port)
