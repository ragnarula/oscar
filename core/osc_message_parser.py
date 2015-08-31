import gevent
from gevent import monkey
monkey.patch_all(thread=False)
from gevent.pool import Pool
from gevent.queue import Queue
from pythonosc.osc_message import OscMessage, ParseError


class OSCMessageParser:

    class RunningState:

        def start(self, parser):
            pass

        def stop(self, parser):
            parser.change_state(OSCMessageParser.READY_STATE)

        def enter(self, parser):
            parser.pool.spawn(parser.run)

        def exit(self, parser):
            pass

    class ReadyState:

        def start(self, parser):
            parser.change_state(OSCMessageParser.RUNNING_STATE)

        def stop(self, parser):
            pass

        def enter(self, parser):
            parser.dgram_queue = Queue()

        def exit(self, parser):
            pass

    RUNNING_STATE = RunningState()
    READY_STATE = ReadyState()

    def __init__(self, pool=None):
        if pool is None:
            self.pool = Pool()
        else:
            self.pool = pool
        self.dgram_queue = None
        self.state = OSCMessageParser.READY_STATE
        self.state.enter(self)
        self.device_msg_handler = None

    def change_state(self, state):
        self.state.exit(self)
        self.state = state
        self.state.enter(self)

    def add_message(self, msg):
        self.dgram_queue.put(msg)

    def start(self):
        self.state.start(self)

    def stop(self):
        self.state.stop(self)

    def run(self):
        while self.state == OSCMessageParser.RUNNING_STATE:
            try:
                dgram = self.dgram_queue.get(timeout=1)
            except gevent.queue.Empty:
                continue
            if dgram is None:
                continue
            self.pool.spawn(self.parse_dgram, dgram)
        print "osc ending"

    def parse_dgram(self, dgram):
        try:
            msg = OscMessage(dgram)
        except ParseError:
            return
        type = msg.path_list.pop()
        if type == "device" and self.device_msg_handler is not None:
            self.device_msg_handler(msg)
