from oslo.config import cfg
from oslo import messaging
import socket


CONF = cfg.CONF

class Service(object):
    
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


def call(topic, ctxt, method, timeout=10, server=None, version='1.0', **kwargs):
    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic, server=server, version=version)
    client = messaging.RPCClient(transport, target)
    cctxt = client.prepare(timeout=timeout)
    return client.call(ctxt, method, **kwargs)

def cast(topic, ctxt, method, server=None, version='1.0', **kwargs):
    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic, server=server, version=version)
    client = messaging.RPCClient(transport, target)
    client.cast(ctxt, method, **kwargs)
 
def cast_fanout(topic, ctxt, method, version='1.0', **kwargs):
    transport = messaging.get_transport(cfg.CONF)
    target = messaging.Target(topic=topic, fanout=True, version=version)
    client = messaging.RPCClient(transport, target)
    client.cast(ctxt=ctxt, method=method, **kwargs)