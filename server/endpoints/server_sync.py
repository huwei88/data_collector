from oslo.config import cfg
from server import  rpc
import shutil
import socket
import yaml

CONF = cfg.CONF

def operator_wrapper(operator):
    def wrapper(self, ctxt, **kwargs):
        if kwargs.pop('hostname') == socket.gethostname():
            return
        operator(self, ctxt, **kwargs)
        with open(CONF.get('option_file'), 'w') as co:
            yaml.dump({'NODES':self.local_options}, co)
        shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))
    return wrapper


class ConfigurationOperator(object):
    
    hostname = socket.gethostname()
    local_options = {}
    
    def __init__(self):
        try:
            with open(CONF.get('option_file'), 'r') as co:
                self.local_options = yaml.safe_load(co)['NODES']
        except:
            self.local_options = {}
            # can not load yaml file error
#             raise
        
    @operator_wrapper
    def add(self, ctxt, **kwargs):
        options = kwargs.pop('options')
        for option in options:
            self.local_options = dict(self.local_options, **option)
            key = option.keys()[0]
            rpc.cast(key, {}, 'option_sync', key, **option)
            
    
    @operator_wrapper
    def remove(self, ctxt, **kwargs):
        option_keys = kwargs.pop('options')
        for key in option_keys:
            if self.local_options.has_key(key):
                self.local_options.__delitem__(key)
    
    @operator_wrapper
    def modify(self, ctxt, **kwargs):
        options = kwargs.pop('options')
        for option in options:
            self.local_options = dict(self.local_options, **option)
        

class MasterServerSync(object):
    
    def sync_request(self, ctxt, **kwargs):
        try:
            with open(CONF.get('option_file'), 'r') as co:
                options = yaml.safe_load(co)
                return options
        except:
            raise
    
    def test(self, ctxt, **kwargs):
        return kwargs