import rpc
from oslo.config import cfg

kwargs={'name':'huwei'}
print rpc.cast(topic='server_sync',server='huwei-X230', ctxt=cfg.CONF,method='modify',kwargs=kwargs)