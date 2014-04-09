from eventlet import event
from eventlet import greenthread
import logging
from server import exceptions
import sys


LOG = logging.getLogger(__name__)


class LoopingCallDone(Exception):
    """Exception to break out and stop a LoopingCall.

    The poll-function passed to LoopingCall can raise this exception to
    break out of the loop normally. This is somewhat analogous to
    StopIteration.

    An optional return-value can be included as the argument to the exception;
    this return-value will be returned by LoopingCall.wait()

    """

    def __init__(self, retvalue=True):
        """:param retvalue: Value that LoopingCall.wait() should return."""
        self.retvalue = retvalue


class LoopingCall(object):
    def __init__(self, f=None, cycle_index=-1, *args, **kw):
        self.args = args
        self.kw = kw
        self.f = f
        self._running = False
        self.cycle_index = cycle_index

    def start(self, interval, initial_delay=None):
        self._running = True
        done = event.Event()

        def _inner():
            if initial_delay:
                greenthread.sleep(initial_delay)
            cycle_counter = 0
            try:
                while self._running:
                    self.f(*self.args, **self.kw)
                    if not self._running:
                        break
                    if self.cycle_index > 0:
                        cycle_counter += 1
                        if cycle_counter >= self.cycle_index:
                            raise exceptions.AttemptsFailure()
                    greenthread.sleep(interval)
            except LoopingCallDone as e:
                self.stop()
                done.send(e.retvalue)
            except Exception:
                LOG.exception('in looping call')
                done.send_exception(*sys.exc_info())
                return
            else:
                done.send(True)

        self.done = done

        greenthread.spawn(_inner)
        return self.done

    def stop(self):
        self._running = False

    def wait(self):
        return self.done.wait()