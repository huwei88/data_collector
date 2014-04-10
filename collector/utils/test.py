import util
from oslo.config import cfg
from collector.modules import basic
import socket


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

kwargs={'files':['../basic.conf,test.py'],'data_names':['basdfsic','test']}

basic.collect_file_content(**kwargs)