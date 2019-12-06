import logging
import logging.config
import logging.handlers
from multiprocessing import Process, Queue, Event, current_process
import os
import random
import time

class LogHandler:
    def handle(self, record):
        if record.name == "root":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(record.name)

        if logger.isEnabledFor(record.levelno):
            record.processName = '%s (for %s)' % (current_process().name, record.processName)
            logger.handle(record)

def listener_process(q, stop_event, config):
    logging.config.dictConfig(config)
    listener = logging.handlers.QueueListener(q, LogHandler())
    listener.start()
    logger = logging.getLogger('setup')
    stop_event.wait()
    listener.stop()

def worker_process(config):
    logging.config.dictConfig(config)
    levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR,
              logging.CRITICAL]
    loggers = ['file', 'console']
    logger = logging.getLogger('setup')

    for i in range(2):
        lvl = random.choice(levels)
        logger = logging.getLogger(random.choice(loggers))
        logger.log(lvl, 'Message no. %d', i)
        time.sleep(0.01)

def main():
    q = Queue()
    config_initial = {
        'version': 1,
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'level': 'INFO',
                'filename':'C:/Data/PXCLogs/alog.log'
            }
        },
        'root': {
            'handlers': ['file'],
            'level': 'DEBUG'
        }
    }

    config_worker = {
        'version': 1,
        'disable_existing_loggers': True,
        'handlers': {
            'queue': {
                'class': 'logging.handlers.QueueHandler',
                'queue': q
            }
        },
        'root': {
            'handlers': ['queue'],
            'level': 'DEBUG'
        }
    }

    config_listener = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'detailed': {
                'class': 'logging.Formatter',
                'format': '%(asctime)s %(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
            },
            'simple': {
                'class': 'logging.Formatter',
                'format': '%(name)-15s %(levelname)-8s %(processName)-10s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'level': 'ERROR'
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'C:/Data/PXCLogs/alog.log',
                'mode': 'w',
                'formatter': 'detailed',
            }
        },
        'loggers': {
            'inst': {
                'handlers': ['file']
            }
        },
        'root': {
            'handlers': ['file'],
            'level': 'DEBUG'
        }
    }
    
    logging.config.dictConfig(config_initial)
    logger = logging.getLogger('setup')
    logger.info('About to create workers ...')
    workers = []
    for i in range(5):
        wp = Process(target=worker_process, name='worker %d' % (i + 1),
                     args=(config_worker,))
        workers.append(wp)
        wp.start()
        logger.info('Started worker: %s', wp.name)
    logger.info('About to create listener ...')
    stop_event = Event()
    lp = Process(target=listener_process, name='listener',
                 args=(q, stop_event, config_listener))
    lp.start()
    logger.info('Started listener')
    
    for wp in workers:
        wp.join()

    logger.info('Telling listener to stop ...')
    stop_event.set()
    lp.join()
    logger.info('All done.')

if __name__ == '__main__':
    main()