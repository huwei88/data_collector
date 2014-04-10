import ConfigParser
from collector import  rpc
import datetime
import hashlib
from oslo.config import cfg
import os
import socket
import threading

opts = [
        cfg.StrOpt('md5_cache_file',
                   default='.md5_cache',
                   help='The file stored the sended data\'s md5.'),
        cfg.StrOpt('section_name',
                   default='data_md5',
                   help='Use Conf file to store and search md5, it is not\
                        a good idea, and it should be replaced to another way.'),
        ]


CONF = cfg.CONF
CONF.register_opts(opts)


class Singleton(object):

    objs = {}
    objs_locker = threading.Lock()

    def __new__(cls, *args, **kv):
        if cls in cls.objs:
            return cls.objs[cls]['obj']

        cls.objs_locker.acquire()
        try:
            ## double check locking
            if cls in cls.objs:
                return cls.objs[cls]['obj']
            obj = object.__new__(cls)
            cls.objs[cls] = {'obj': obj, 'init': False}
            setattr(cls, '__init__', cls.decorate_init(cls.__init__))
        finally:
            cls.objs_locker.release()

    @classmethod
    def decorate_init(cls, fn):
        def init_wrap(*args):
            if not cls.objs[cls]['init']:
                fn(*args)
                cls.objs[cls]['init'] = True
            return

        return init_wrap


def data_changed(name, id):
    cf = ConfigParser.ConfigParser()
    if not os.path.exists(CONF.get('md5_cache_file')):
        with open(CONF.get('md5_cache_file'), 'w') as f:
            cf.add_section(CONF.get('section_name'))
            cf.write(f)
        return True
    cf.read(CONF.get('md5_cache_file'))
    try:
        cf.get(CONF.get('section_name'), id)
        return False
    except ConfigParser.NoOptionError:
        cf.set(CONF.get('section_name'), name, id)
        with open(CONF.get('md5_cache_file'), 'w') as f:
            cf.write(f)
        return True


def send_data(fun):
    def wrapper(**kwargs):
        contents = fun(**kwargs)
        data_names = kwargs.pop('data_names')
        index = 0
        for content in contents:
            md5 = hashlib.md5()
            md5.update(content)
            ID = md5.hexdigest()
            if data_changed(data_names[index], ID):
                con = content
            else:
                con = ''
            wrapped_data = {'name': data_names[index],
                            'date': get_local_date(), 'content': con,
                            'id': ID, 'hostname': socket.gethostname(),
                            'storage_driver': 'default'}
            rpc.cast(topic=CONF.get('server_topic'),
                     ctxt={}, method='store_data',
                     **wrapped_data)
            index = index + 1
    return wrapper


def get_file_Md5(strFile):
    try:
        dst_file = open(strFile, "rb")
        md5 = hashlib.md5()
        strRead = ""

        while True:
            strRead = dst_file.read(8096)
            if not strRead:
                break
            md5.update(strRead)
        #read file finish
        strMd5 = md5.hexdigest()
    finally:
        if dst_file:
            dst_file.close()
    return strMd5


def get_local_date():
    date_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.now().strftime(date_format)


def get_utc_date():
    date_format = '%Y-%m-%d %H:%M:%S'
    return datetime.datetime.utcnow().strftime(date_format)