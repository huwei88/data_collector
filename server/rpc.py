from oslo.config import cfg
from oslo import messaging

url = "qpid://127.0.0.1:5672"
transport = messaging.get_transport(cfg.CONF,url=url)

def call(topic, ctxt, method, timeout=10, server=None, version='1.0', **kwargs):
    target = messaging.Target(topic=topic, server=server, version=version)
    client = messaging.RPCClient(transport, target)
    return client.call(ctxt, method, **kwargs)

def cast(topic, ctxt, method, server=None, version='1.0', **kwargs):
    target = messaging.Target(topic=topic, server=server, version=version)
    client = messaging.RPCClient(transport, target)
    client.cast(ctxt, method, **kwargs)
 
def cast_fanout(topic, ctxt, method, version='1.0', **kwargs):
    target = messaging.Target(topic=topic, fanout=True, version=version)
    client = messaging.RPCClient(transport, target)
    client.cast(ctxt=ctxt, method=method, **kwargs)