# from __future__ import absolute_import
# from celery import shared_task, Task
# from gevent.lock import BoundedSemaphore
# from gevent import monkey; monkey.patch_all()
# from gevent.pool import Pool
# from core.async_udp_server import AsyncUDPServer
# from core.osc_message_parser import OSCMessageParser
# from core.connection_manager import ConnectionManager
#
#
# class CoreTask():
#
#     abstract = True
#     running = False
#     sem = BoundedSemaphore(1)
#
#     pool = Pool()
#     udp_server = AsyncUDPServer('', 6060, pool=pool)
#     osc_message_parser = OSCMessageParser(pool=pool)
#     connection_manager = ConnectionManager(pool=pool)
#     udp_server.msg_handler = osc_message_parser.add_message
#     osc_message_parser.device_msg_handler = connection_manager.send_osc_message
#
#     def __init__(self):
#         print 'INIT'
#         if not CoreTask.running:
#             CoreTask.sem.acquire()
#             CoreTask.udp_server.start()
#             CoreTask.osc_message_parser.start()
#             CoreTask.connection_manager.start()
#             CoreTask.running = True
#             CoreTask.sem.release()
#         self.connection_manager = CoreTask.connection_manager
#
#
# @shared_task(base=CoreTask)
# def control_task(type, device):
#     if type is "UP":
#         control_task.connection_manager.update(device)
#     if type is "DEL":
#         control_task.connection_manager.delete(device)
