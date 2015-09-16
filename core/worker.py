from __future__ import absolute_import
from celery import shared_task
from celery.signals import celeryd_init
from gevent.lock import BoundedSemaphore
from oscar.celeryapp import app
from gevent import monkey; monkey.patch_all()
import gevent
from gevent.pool import Pool
from gevent.queue import Queue
from core.async_udp_server import AsyncUDPServer
from core.osc_message_parser import OSCMessageParser
from core.connection_manager import ConnectionManager
import signal, os
import logging


def get_oscar_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join('/var/log/oscar/core.log'), 'w')
    logger.addHandler(handler)
    return logger

running = False
queue = Queue()
sem = BoundedSemaphore(1)

@shared_task
def stop_server():
    queue.put("STOP")


@shared_task
def stop_and_kill():
    queue.put("STOP")
    os.kill(os.getpid(), signal.SIGINT)


@shared_task
def run_server():
    global running
    global queue
    sem.acquire()
    if running:
        print "Task already running!"
        sem.release()
        return

    app.control.purge()
    queue = Queue()
    running = True
    sem.release()

    pool = Pool()
    udp_server = AsyncUDPServer('', 6060, pool=pool, logger_factory=get_oscar_logger)
    osc_message_parser = OSCMessageParser(pool=pool)
    connection_manager = ConnectionManager(pool=pool, logger_factory=get_oscar_logger)

    udp_server.msg_handler = osc_message_parser.add_message
    osc_message_parser.device_msg_handler = connection_manager.send_osc_message

    udp_server.start()
    osc_message_parser.start()
    connection_manager.start()

    while running:
        try:
            msg = queue.get(timeout=1)
        except gevent.queue.Empty:
            continue
        if msg == "STOP":
            print "Received STOP"
            break
        if msg['type'] is "UP":
            connection_manager.update(msg['device'])
        if msg['type'] is "DEL":
            connection_manager.delete(msg['device'])

    udp_server.stop()
    osc_message_parser.stop()
    connection_manager.stop()

    pool.join()


@shared_task
def update_device(device):
    queue.put({'type': 'UP', 'device': device})


@shared_task
def delete_device(device):
    queue.put({'type': 'DEL', 'device': device})


@celeryd_init.connect
def startup(**kwargs):
    run_server.delay()
