import datetime
import hashlib
import threading


class Singleton(object):
   
    objs  = {}
    objs_locker =  threading.Lock()

    def __new__(cls, *args, **kv):
        if cls in cls.objs:
            return cls.objs[cls]['obj']

        cls.objs_locker.acquire()
        try:
            if cls in cls.objs: ## double check locking
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





def get_file_Md5(strFile):
    try:
        dst_file = open(strFile, "rb");
        md5 = hashlib.md5();
        strRead = "";
        
        while True:
            strRead = dst_file.read(8096);
            if not strRead:
                break;
            md5.update(strRead);
        #read file finish
        strMd5 = md5.hexdigest();
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