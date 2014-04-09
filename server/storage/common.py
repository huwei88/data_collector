from oslo.config import cfg
from server.utils import import_utils

store_opts = [cfg.StrOpt('store_driver',
                         default='%.sql_alchemy' % __package__,
                         help='Define which driver will be used to \
                         store the data.'),
              ]

CONF = cfg.CONF
CONF.register_opts(store_opts)


class Data(object):
    
    def __init__(self):
        return


class Host(object):
    
    def __init__(self):
        return


_STORAGE_DRIVER = None

def save_data(data):
    return _get_imp().save_data(data)


def search_data():
    return _get_imp().search_data()

def _get_imp():
    global _STORAGE_DRIVER
    if not _STORAGE_DRIVER:
        _STORAGE_DRIVER = import_utils.import_module(CONF.get('store_driver'))
    else:
        return _STORAGE_DRIVER
    