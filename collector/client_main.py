import endpoints
from oslo.config import cfg
import socket
import rpc
import thread
from utils import task_manager, util, import_utils
import yaml


collector_opts = [
                  cfg.StrOpt('option_file',
                  default = 'collector.yaml',
                  help = 'The file stored the options download from server.')
                  ]

rpc_opts = [
            cfg.StrOpt('server_topic',
                       default = 'server',
                       help = 'Each server will listen on this topic.'),
            cfg.StrOpt('all_client_topic',
                       default = 'collector',
                       help = 'Topic used for sync between servers'),
            cfg.StrOpt('client_topic',
                       default = socket.gethostname(),
                       help = 'Topic used for request options sync when the normal server startup.'),
            cfg.IntOpt('timeout',
                       default = '20',
                       help = 'Timeout before get the server\'s response'),
            ]
CONF=cfg.CONF
CONF()
CONF.register_opts(rpc_opts)
CONF.register_opts(collector_opts)




class DriverManager(util.Singleton):
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
                ymal_options = yaml.load(option_file)['configurations']
                self.add_drivers(ymal_options)
            except:
                raise
    
    def add_drivers(self, drivers={}):
        """
        params drivers: A dict that contains some collect functions information.
            The struct of the dict must be the same with the one in collector.yaml.
        """
        for name, option in drivers.items():
            self.options = dict(self.options, **{name: option})
            kwargs = option.pop('kwargs')
            path = option.pop('path')
            name = option.pop('name')
            data_names = option.pop('data_names')
            kwargs = dict(kwargs, **data_names)
            cycle_str = option.pop('cycle').lower()
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
                collect_fun = import_utils.import_class('modules.'+path)
            except ImportError:
                try:
                    collect_fun = import_utils.import_class('user_modules.'+path)
                except ImportError:
                    # log error msg.
                    raise
            p_task = task_manager.PeriodicTask(interval=cycle, f=collect_fun, name=name, **kwargs)
            self.manager.add_task(p_task)
            
    def remove_drivers(self, drivers={}):
        """
        param drivers: A list of drivers that will be deleted from
            the self.options.
        type drivers: list, the element is a dict. At least it should
            contain the 'name' key. E.g. {'name': 'test',}
        """
        for name, option in drivers.items():
            self.options.pop(name)
            self.manager.remove_task(name)
    
    def modify_drivers(self, drivers={}):
        for name, option in drivers.items():
            if not self.options.has_key(name):
                # It should raise an error there is no driver in self.options.
                # Or at least it should log a warning message to log.
                raise 
                # drivers.pop(name)
        self.remove_drivers(drivers)
        self.add_drivers(drivers)
    
    def start(self):
        self.manager.wait()
    
    def stop(self):
        self.manager.stop()


def client_init():
    thread.start_new_thread(rpc.Service(CONF.get('client_topic'),
                                [endpoints.ServerClient,]).start,())
    # Need to change the sync strategy.
    kwargs = {'hostname': socket.gethostname()}
    options = rpc.call(topic=CONF.get('server_topic'), ctxt={}, method='get_option', **kwargs)
    with open(CONF.get('option_file'), 'w') as f:
        yaml.dump({'configurations': options}, f)
    

if __name__ == '__main__':
    client_init()







