from datetime import datetime

import eventlet

class AlreadyExistTasknameError(Exception):
    '''
    Raising it if the task manager has
    already registed the same task
    '''
    _error_msg = '''Duplicate task name error! The task name of %s has already exist.'''
    
    def __init__(self, task_name):
        super(AlreadyExistTasknameError, self).__init__(self._error_msg % task_name)

class TaskTimeError(Exception):
    '''
    Raising it if the task spend longer time
    than the interval time.
    '''
    _error_msg = '''The task name of %s spend long time than expected.'''
    
    def __init__(self, task_name):
        super(TaskTimeError, self).__init__(self._error_msg % task_name)
    
    
class PeriodicTask(object):
    '''
    Periodic task.
    '''
    def __init__(self, interval, f, task_name=None, *arg, **kwargs):
        self.interval=interval
        self._f = f
        self._arg = arg
        self._task_name = task_name or f.__name__
        self._kw = kwargs
        self._stop_running = False
        
    def get_task_name(self):
        return self._task_name
    
    def run(self):
        '''
        Invoking the callback method, if it spends
        longer time than the interval it provide,
        the TaskTimeError will be triggered.
        '''
        while not self._stop_running:
            before = datetime.utcnow()
            self._f(*self._arg, **self._kw)
            after = datetime.utcnow()
            delta_seconds = (after -before).total_seconds()
            if delta_seconds > self.interval:
                raise TaskTimeError(self._task_name)
            else:
                sleep_time = self.interval - delta_seconds
                eventlet.sleep(sleep_time)
    
    def stop(self):
        self._stop_running = True


class TaskManager(object):
    '''
    Manage all the periodic task, and track it.
    '''
    def __init__(self):
        self.runing = False
        self.tasks = []
        self.pool = eventlet.GreenPool(size=100)
    
    def _get_task(self, task_name):
            for task in self.tasks:
                if task.get_task_name() == task_name:
                    return task
            return None
    
    def add_tasks(self, tasks):
        for task in tasks:
            self.add_task(task)
    
    def add_task(self, task):
        if not self._get_task(task.get_task_name()):
            self.tasks.append(task)
            self.pool.spawn(task.run)
        else:
            raise AlreadyExistTasknameError(task.get_task_name())
    
    def remove_task(self, task_name=None):
        '''
        This method is just let the periodic task exit the loop,
        and remove it from the list.
        '''
        task = self._get_task(task_name)
        if task:
            self.tasks.remove(task)
            task.stop()
        
    def wait(self):
        self.pool.waitall()


def print_name(*arg,**kwargs):
    print arg
    print kwargs
 
 
 
 
# arg1=['huwei']
# arg2=['xtdxhw']
# kw1={'name':'huwei'}
# kw2={'name':'xtdxhw'}
# task1=PeriodicTask(1, print_name,'asdf',*arg1, **kw1)
# task2=PeriodicTask(2, print_name,'werqwer',*arg2, **kw2)
# manager=TaskManager()
# manager.add_task(task1)
# manager.add_task(task2)
# manager.wait()
