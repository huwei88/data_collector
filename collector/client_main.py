import endpoints
from oslo.config import cfg
import socket
import rpc
import thread
from utils import task_manager, import_utils
import yaml


# hostname = socket.gethostname()
hostname = 'huwei_pc'

collector_opts = [
                  cfg.StrOpt('option_file',
                  default='collector.yaml',
                  help='The file stored the options download from server.')
                  ]

rpc_opts = [
            cfg.StrOpt('host_ID',
                       default=hostname,
                       help='The identity which can distinguish the node from\
                       others.'),
            cfg.StrOpt('server_topic',
                       default='server',
                       help='Each server will listen on this topic.'),
            cfg.StrOpt('all_client_topic',
                       default='collector',
                       help='Topic used for sync between servers'),
            cfg.StrOpt('client_topic',
                       default=hostname,
                       help='Topic used for request options sync when the\
                       normal server startup.'),
            cfg.IntOpt('timeout',
                       default='20',
                       help='Timeout before get the server\'s response'),
            ]

CONF = cfg.CONF
CONF()
CONF.register_opts(rpc_opts)
CONF.register_opts(collector_opts)


#class DriverManager(util.Singleton):
class DriverManager(object):
    """
    This class is for collect driver initialization.
    The driver can be added or removed without stop
    client main thread.
    """

    manager = task_manager.TaskManager()

    def __init__(self):
        self.options = {}
        with open(CONF.get('option_file'), 'r') as option_file:
            try:
                yaml_options = yaml.safe_load(option_file)['configurations']
                self.add_drivers(yaml_options)
            except:
                raise

    def add_drivers(self, drivers=[], local_options=None):
        """
        params drivers: A list contains all the configuration about this node.
            type: List
        """
        if local_options:
            self.options = local_options
        for driver in drivers:
            kwargs = driver['kwargs']
            collect_driver = driver['collect_driver']
            data_names = driver['data_names']
            cycle = driver['cycle']
            storage_driver = driver['storage_driver']
            kwargs = dict(kwargs, **{'storage_driver': storage_driver})
            kwargs = dict(kwargs, **{'data_names': data_names})
            self.options = dict(self.options, **driver)
            cycle_str = cycle.lower()
            num = cycle_str[:-1]
            unit = cycle_str[-1]
            try:
                cycle = int(num)
            except:
                #log
                raise
            if unit == 'm':
                cycle = cycle * 60
            elif unit == 'h':
                cycle = cycle * 3600
            elif unit == 's':
                pass
            else:
                # log
                raise

            try:
                collect_fun = import_utils.import_class(
                                'modules.' + collect_driver)
            except ImportError:
                try:
                    collect_fun = import_utils.import_class(
                                    'modules.' + collect_driver)
                except ImportError:
                    # log error msg.
                    raise
            p_task = task_manager.PeriodicTask(interval=cycle, f=collect_fun,
                                               name=driver['name'], **kwargs)
            self.manager.add_task(p_task)

    def remove_drivers(self, drivers=[], local_options=None):
        """
        param drivers: A list of driver names that will be deleted from
            the self.options.
        type drivers: list, the element is string.
        """
        if local_options:
            self.options = local_options
        for name in drivers:
            self.manager.remove_task(name)

    def modify_drivers(self, drivers=[], local_options=None):
        if local_options:
            self.options = local_options
        for option in drivers:
            self.manager.remove_task(option['name'])
        self.add_drivers(drivers, local_options)

    def start(self):
        self.manager.wait()

    def stop(self):
        self.manager.stop()

    def pause(self):
        self.manager.pause()


def client_init():
    thread.start_new_thread(rpc.Service(CONF.get('client_topic'),
                                [endpoints.ServerClient(),]).start,())

    # Need to change the sync strategy.
    kwargs = {'hostname': hostname}
    options = rpc.call(topic=CONF.get('server_topic'), ctxt={}, method='get_option', **kwargs)
    with open(CONF.get('option_file'), 'w') as f:
        yaml.safe_dump({'configurations': options}, f)

driverManager = None

if __name__ == '__main__':
    client_init()
#     global driverManager
    driverManager = DriverManager()
    driverManager.start()

