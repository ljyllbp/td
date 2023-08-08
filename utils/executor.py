import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

class Executor(object):
    def __init__(self, thread_nums=4):
        self._executor = ThreadPoolExecutor(max_workers=thread_nums)

    def execute(self, func, *arg):
        """
        多线程任务执行
        :param func:
        :param arg:
        :return:
        """
        if arg:
            if isinstance(arg[0], tuple):
                return self._executor.submit(func, *arg[0])
            else:
                return self._executor.submit(func, arg[0])
        else:
            return self._executor.submit(func)