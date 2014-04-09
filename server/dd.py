from endpoints import server_sync, client_request
import thread
from utils import util, task_manager
import os
from oslo.config import cfg
from oslo import messaging
import rpc
import socket
import shutil
import yaml
import eventlet


basic_opts = [
              cfg.StrOpt('role',
                         default = 'master',
                         help = 'Assign the host role, master or normal'),
              cfg.StrOpt('option_file',
                         default = 'ClientOption.yaml',
                         help = 'The file stored the client options'),
              cfg.StrOpt('option_cache_file',
                         default = '.ClientOption.yaml',
                         help = 'The cache file stored the before last changed client options.'),
              ]

rpc_opts = [
            cfg.StrOpt('server_topic',
                       default = 'server',
                       help = 'Each server will listen on this topic.'),
            cfg.StrOpt('master_server_topic',
                       default = 'server_master',
                       help = 'Topic used for request options sync when the normal server startup.'),
            cfg.IntOpt('timeout',
                       default = '20',
                       help = 'Timeout before get the server\'s response'),
            ]

CONF = cfg.CONF
CONF()
CONF.register_opts(basic_opts)
CONF.register_opts(rpc_opts)
taskManager = task_manager.TaskManager()


class ServerListener(object):
    
    version = '1.0'
    
    def __init__(self, topic, endpoints):
        self.hostname = socket.gethostname()
        self.topic = topic 
        self.transport = messaging.get_transport(cfg.CONF)
        self.target = messaging.Target(topic=self.topic, server=self.hostname, version=self.version)
        self.endpoints = endpoints 
        self.server = messaging.get_rpc_server(self.transport, self.target, self.endpoints)
        
    def start(self):
        self.server.start()
        
    def stop(self):
        self.server.stop()
        
# pool = eventlet.GreenPool()
# pool.spawn(ServerListener('test',[server_sync.MasterServerSync(),]).start)
# pool.spawn(ServerListener('test1',[server_sync.MasterServerSync(),]).start)
# pool.waitall()

kwargs0={'topic_':'test'}
kwargs1={'topic_':'test1'}
print rpc.call(topic='test',ctxt={},method='option_add',server='huwei-X230',**kwargs1)
print rpc.call(topic='test1',ctxt={},method='option_add',**kwargs1)
