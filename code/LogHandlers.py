import logging
import logging.config
import logging.handlers
from multiprocessing import current_process
import time
import os
from datetime import datetime as dt


class LogHandler:
    def __init__(self):
        if not os.path.exists(r'C:/Data/PXCLogs'):
            os.makedirs(r'C:/Data/PXCLogs')
        self.logpath = 'C:/Data/PXCLogs/PxcSession_{:s}.log'.format(dt.strftime(dt.now(),'%Y-%m-%d_%H-%M-%S'))
    def handle(self, record):

        logger = logging.getLogger(record.name)

        if logger.isEnabledFor(record.levelno):
            record.processName = '%s' % (record.processName)
            logger.handle(record)
            

def logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)

def worker_process(config):
    logging.config.dictConfig(config)
    logger = logging.getLogger('setup')
    logger.critical('setmeup')

    for i in range(2):
#        logger = logging.getLogger(random.choice(loggers))
        logger = logging.getLogger('asdf')
        logger.log(logging.WARNING, 'Message no. %d', i)
        time.sleep(0.01)