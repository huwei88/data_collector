from endpoints import server_sync
import thread
from utils import util, task_manager
import os
from oslo.config import cfg
from oslo import messaging
import rpc
import socket
import shutil
import yaml

# CLIENT_OPTION = 'ClientOption.yaml'
# CLIENT_OPTION_OLD='.ClientOption.yaml'
# SERVER_SYNC_TOPIC = 'server_sync'
# MASRER_SERVER_TOPIC = 'server_master'


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

rpc_opts = [cfg.StrOpt('amqp_url',
                       default = 'qpid://127.0.0.1:5672',
                       help = 'Default amqp url'),
            cfg.StrOpt('server_sync_topic',
                       default = 'server_sync',
                       help = 'Topic used for sync between servers'),
            cfg.StrOpt('master_server_topic',
                       default = 'server_master',
                       help = 'Topic used for request options sync when the normal server startup.'),
            cfg.IntOpt('timeout',
                       default = '20',
                       help = 'Timeout before get the server\'s response'),
            ]

CONF = cfg.CONF
CONF.register_opts(basic_opts)
CONF.register_opts(rpc_opts)
taskManager = task_manager.TaskManager()


class ServerListener(object):
    
    version = '1.0'
    
    def __init__(self, topic, endpoints):
        self.hostname = socket.gethostname()
        self.topic = topic 
        self.transport = messaging.get_transport(cfg.CONF, url="qpid://127.0.0.1:5672")
        self.target = messaging.Target(topic=self.topic, server=self.hostname, version=self.version)
        self.endpoints = endpoints 
        self.server = messaging.get_rpc_server(self.transport, self.target, self.endpoints)
        
    def start(self):
        self.server.start()
        
    def stop(self):
        self.server.stop()

def wrap_option(options):
    hostname = socket.gethostname()
    date = util.get_local_date()
    return {'hostname':hostname, 'date': date,
            'options':options}

def check_configurations():
    modify = []
    remove = []
    add = []
    new_conf = open(CONF.get('option_file'), 'r')
    old_conf = open(CONF.get('option_cache_file'), 'r')
    try:
        new = yaml.safe_load(new_conf) 
        old = yaml.safe_load(old_conf) 
    except:
        # need to log the error msg
        raise 
    new_conf.close()
    old_conf.close()
    new_nodes = new['NODES']
    old_nodes = old['NODES']
    new_keys = new_nodes.keys()
    old_keys = old_nodes.keys()
    for key in new_keys:
        try:
            old_value = old_nodes[key]
            if old_value != new_nodes[key]:
                modify.append({key:new_nodes[key]})
        except KeyError:
            add.append({key:new_nodes[key]})
    for key in old_keys:
        if key not in new_keys:
            remove.append(key)
    if remove:
        print remove
        print 'remove'
        rpc.cast_fanout(topic=CONF.get('server_sync_topic'),
                        ctxt=cfg.CONF, method='remove', **wrap_option(remove))
    if add:
        print add
        print 'add'
        rpc.cast_fanout(topic=CONF.get('server_sync_topic'),
                        ctxt=cfg.CONF, method='add', **wrap_option(add))
    if modify:
        print modify
        print 'modify'
        rpc.cast_fanout(topic=CONF.get('server_sync_topic'),
                        ctxt=cfg.CONF, method='modify', **wrap_option(modify))         


def configuration_monitor():
    if not os.path.exists(CONF.get('option_file')):
        open(CONF.get('option_file'), 'w').close()
        return
    if not os.path.exists(CONF.get('option_cache_file')):
        shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))
        return
    if util.get_file_Md5(CONF.get('option_file')) != util.get_file_Md5(CONF.get('option_cache_file')):
        check_configurations()
        shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))


def master_init():
    configuration_monitor_task = task_manager.PeriodicTask(2, configuration_monitor,
                                     'configuration_monitor_task')
    taskManager.add_task(configuration_monitor_task)
    thread.start_new_thread(ServerListener(CONF.get('master_server_topic'),
                                           [server_sync.MasterServerSync(),]).start, ())
    
def normal_init():
    ''' Send a request to master to sync the configurations. '''
    thread.start_new_thread(ServerListener(CONF.get('server_sync_topic'), [server_sync.ConfigurationOperator(),]).start,())
    options = rpc.call(CONF.get('master_server_topic'), cfg.CONF, 'sync_request')
    with open(CONF.get('option_file'), 'w') as f:
        yaml.dump(options, f)
    
def server_init():
    if CONF.get('role') == 'master':
        master_init()
    else:
        normal_init()
    taskManager.wait()

print CONF.get('transport_url')

# if __name__== '__main__':
#     server_init()
    
