import socket
import yaml


CLIENT_OPTION = 'ClientOption.yaml'
CLIENT_OPTION_OLD='.ClientOption.yaml'


class ClientRequest(object):
    
    hostname = socket.gethostname()
    local_options = None
    
    def __init__(self):
        try:
            with open(CLIENT_OPTION, 'r') as co:
                self.local_options = yaml.safe_load(co)['NODES']
        except:
            self.local_options = {}
            # can not load yaml file error
#             raise
    
    def get_option(self, ctxt, **kwargs):
        hostname = kwargs.pop('hostname')
        if not self.local_options.has_key(hostname):
            return None
        else :
            return self.local_options[hostname]
    
    def store_data(self, ctxt, **kwargs):
        raise NotImplementedError
    
