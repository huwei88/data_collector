from exceptions import *
from endpoints import server_sync, client_request
import logging
import thread
from utils.third_party_code import LoopingCallDone
from utils.third_party_code import LoopingCall
from utils import util, task_manager
import os
from oslo.config import cfg
import rpc
import socket
import shutil
import yaml

LOG = logging.getLogger(__name__)


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
            cfg.IntOpt('wait_time',
                       default=10,
                       help='The waiting time before sending a update request message to a client\
                       after sent the changed data to servers.')
            ]

log_opts = [
            cfg.BoolOpt('verbose',
                       default=True,
                       help='If it is true, the log level will be info'),
            cfg.BoolOpt('debug',
                       default=False,
                       help='If it is true, the log level will be Debug'),
            cfg.StrOpt('log_format',
                       default='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                       help='Log format.'
                       ),
            cfg.StrOpt('log_dir',
                       default='/var/log/collector',
                       help='The log directory'),
            cfg.StrOpt('log_file',
                       default='server.log',
                       help='The log file name'),
            cfg.StrOpt('log_datefmt',
                       default='%m-%d %H:%M',
                       help='Log data format')
            ]


CONF = cfg.CONF
CONF()
CONF.register_opts(basic_opts)
CONF.register_opts(rpc_opts)
CONF.register_opts(log_opts)
taskManager = task_manager.TaskManager()


def wrap_option(options):
    hostname = socket.gethostname()
    date = util.get_local_date()
    return {'hostname':hostname, 'date': date,
            'options':options}


class Server(object):

    def __init__(self):
        CONF.set_override('role','master')
        if CONF.get('role') == 'master':
            self.role = 'master'
            self.topic = CONF.get('server_topic')
        else:
            self.topic = CONF.get('master_server_topic')
            self.role = 'normal'
            CONF.set_override('option_file', 'ClientOption_normal.yaml')
        configuration_monitor_task = task_manager.PeriodicTask(2, self.configuration_monitor,
                                         'configuration_monitor_task')
        taskManager.add_task(configuration_monitor_task)

    def master_init(self):
        thread.start_new_thread(rpc.Service(
        									CONF.get('master_server_topic'),
                                            [server_sync.MasterServerSync(),
        									server_sync.ConfigurationOperator(),
        									]
										).start,()
							   )

    def normal_init(self):
        ''' Send a request to master to sync the configurations. '''
        thread.start_new_thread(rpc.Service(CONF.get('server_topic'),
                                               [server_sync.ConfigurationOperator(),
                                                client_request.ClientRequest()],).start,())
        def sync_requests(topic):
            try:
                options = rpc.call(topic, {}, 'sync_request')
                with open(CONF.get('option_file'), 'w') as f:
                    yaml.safe_dump(options, f)
                raise LoopingCallDone()
            except:
                LOG.warn("timeout to connect to server.")

        try:
         	LoopingCall(f=sync_requests, cycle_index=10,topic=self.topic).start(1, 0)
        except AttemptsFailure:
			Log.error("Failed to synchronized from master after tried 10 times to connect master server.")

    def start_service(self):
#         import pdb;pdb.set_trace()
        if CONF.get('role') == 'master':
            self.master_init()
        else:
            self.normal_init()
    	taskManager.wait()

    def configuration_monitor(self):
        if not os.path.exists(CONF.get('option_file')):
            open(CONF.get('option_file'), 'w').close()
            return
        if not os.path.exists(CONF.get('option_cache_file')):
            shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))
            return
        if util.get_file_Md5(CONF.get('option_file')) != util.get_file_Md5(CONF.get('option_cache_file')):
            self.check_configurations()
            shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))

    def check_configurations(self):
        """
        For servers synchronization.
        """
        modify = []
        remove = []
        add = []
        updated_host = []
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
                    if key not in updated_host:
                        updated_host.append(key)
            except KeyError:
                add.append({key:new_nodes[key]})
                if key not in updated_host:
                    updated_host.append(key)
        for key in old_keys:
            if key not in new_keys:
                remove.append(key)
                if key not in updated_host:
                    updated_host.append(key)
        if remove:
            rpc.cast_fanout(topic=self.topic,
                            ctxt={}, method='remove',
                            **wrap_option(remove))
        if add:
            rpc.cast_fanout(topic=self.topic,
                            ctxt={}, method='add',
                            **wrap_option(add))
        if modify:
            rpc.cast_fanout(topic=self.topic,
                            ctxt={}, method='modify',
                            **wrap_option(modify))

        # Let's send the need update clients to master.
        if self.role != 'master' and updated_host:
            rpc.cast_fanout(topic=self.topic,
                            ctxt={}, method='notify_clients',
                            **{'clients': updated_host})
        elif self.role == 'master' and updated_host:
            server_sync.client_sync_request(updated_host)


def init_logger():
    level = logging.WARNING
    if CONF.get('debug'):
        level = logging.DEBUG
    if CONF.get('verbose'):
        level = logging.INFO

    logging.basicConfig(level=level,
                        format=CONF.get('log_format'),
                        datefmt=CONF.get('log_datefmt'),
                        filename=CONF.get('log_file'),
                        filemode='a')

    # debug code
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)



if __name__== '__main__':
#     init_logger()
    Server().start_service()
