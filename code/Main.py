import multiprocessing as mp
import ExpController as ec
import ExpGUI as eg
import logging
import os
from datetime import datetime as dt
import LogHandlers as lh
import importlib
import time
import threading
importlib.reload(logging)
#from lib import Apparatus as ap

if __name__ == "__main__":
    mp.current_process().name = 'root'
    
    with ec.ExpManager() as manager:        # Generate a manager of this custom type
        instReqQ = manager.Queue()          # Set up queues for communicating between processes during runs
        fileReqQ = manager.Queue()
        logQ = manager.Queue(-1)
               
        exp = manager.ExpController()       # Build a custom data storage object within the manager
        
        
        ####### SET UP LOGGING #######
        d = {
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
                'level': 'INFO',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'C:/Data/PXCLogs/alog.log',
                'mode': 'w',
                'formatter': 'detailed',
                'level': 'DEBUG'
            },
        },
        'loggers': {
            'gui': {
                'handlers': ['console']
            },
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['file']
        },
    }          
        
                    
        logging.config.dictConfig(d)
        listener = logging.handlers.QueueListener(logQ, lh.LogHandler())
        listener.start()
        
        
        ### GET THIS PARTY STARTED ###
        
        print('Code Version {:s}'.format(exp.get_version()))
        print('Running on {:d} CPUs'.format(mp.cpu_count()))
        
       # START YOUR ENGINES
        gui = eg.ExpGUI(exp, instReqQ, fileReqQ, logQ)  # Build the GUI        
        gui.startGUI()

        mp.stop_event.wait()
        listener.stop()
        
        logging.shutdown()