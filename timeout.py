import time
import multiprocessing
import logging
import functools

logging.getLogger(__name__).addHandler(logging.NullHandler())


class TimeoutException(Exception):
    pass
    ''' The function took too long to execute '''


class RunnableProcessing(multiprocessing.Process):
    ''' Run a function in a child process. Pass back any exception received'''
    def __init__(self, func, *args, **kwargs):
        self.queue = multiprocessing.Queue(maxsize=1)
        args = (func,) + args
        multiprocessing.Process.__init__(self, target=self.run_func, args=args, kwargs=kwargs)

    def run_func(self, func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
            self.queue.put((True, result))
        except Exception as e:
            self.queue.put((False, e))

    def done(self):
        return self.queue.full()

    def result(self):
        return self.queue.get()


def timeout(seconds, force_kill=True):
    ''' Timeout decorator using Python multiprocessing.
    Courtesy of http://code.activestate.com/recipes/577853-timeout-decorator-with-multiprocessing/
    '''
    def wrapper(function):
        @functools.wraps(function)
        def inner(*args, **kwargs):
            now = time.time()
            proc = RunnableProcessing(function, *args, **kwargs)
            proc.start()
            proc.join(seconds)
            if proc.is_alive():
                if force_kill:
                    proc.terminate()
                runtime = time.time() - now
                logging.info("The function %s timed out after %s seconds", function.__name__, runtime)
                raise TimeoutException('Timed out after {0} seconds'.format(runtime))
            assert proc.done()
            success, result = proc.result()
            if success:
                return result
            else:
                raise result
        return inner
    return wrapper


def evaluate(seconds, function, *args, **kwargs):
    @timeout(seconds)
    def timed_function(*args, **kwargs):
        logging.debug("Started timed evaluation of function '%s(%s)'", function.__name__, *args)
        return function(*args, **kwargs)
    return timed_function(*args, **kwargs)
