from oslo.config import cfg
import logging
from server import  rpc
import shutil
import socket
import thread
import time
import yaml


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def client_sync_request(updated_host):
        """
        For clients synchronization.
        """
        if not updated_host:
            return

        def send_request():
            time.sleep(CONF.get('wait_time'))
            for host in updated_host:
                rpc.cast(topic=host, ctxt={}, method='option_sync')
        thread.start_new_thread(send_request, ())


def operator_wrapper(operator):
    def wrapper(self, ctxt, **kwargs):
#         if kwargs.pop('hostname') == socket.gethostname():
#             return
        operator(self, ctxt, **kwargs)
        with open(CONF.get('option_file'), 'w') as co:
            yaml.safe_dump({'NODES':self.local_options}, co)
        shutil.copy(CONF.get('option_file'), CONF.get('option_cache_file'))
        if CONF.get('role') == 'master':
            """
            If this is a update message come from normal server,
            the master must tell another normal servers to update.
            """
            rpc.cast_fanout(CONF.get('server_topic'), ctxt={}, method=operator.__name__, **kwargs)
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
#         for option in options:
#             key = option.keys()[0]
#             if self.local_options.has_key(key):
#                 options.__delitem__(key)
        for option in options:
            self.local_options = dict(self.local_options, **option)

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

    def get_option(self, ctxt, **kwargs):
        hostname = kwargs.pop('hostname')
        if not self.local_options.has_key(hostname):
            return None
        else :
            return self.local_options[hostname]['modules']


class MasterServerSync(object):

    def sync_request(self, ctxt, **kwargs):
        try:
            with open(CONF.get('option_file'), 'r') as co:
                options = yaml.safe_load(co)
                return options
        except:
            raise

    def sync_ack(self, ctxt, **kwargs):
        """
        Each time the server send a message, the destination host
        should return a message to claim that it has already got the
        message.
        """
        return

    def notify_clients(self, ctxt, **kwargs):
        client_sync_request(kwargs.pop('clients'))
