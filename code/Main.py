import platform
import multiprocessing as mp
import ExpController as ec
import ExpGUI as eg
import logging
import LogHandlers as lh
import sys
import importlib
import matplotlib
from datetime import datetime as dt
import pyvisa
import os

matplotlib.use("TkAgg")


importlib.reload(logging)

if __name__ == "__main__":
    mp.current_process().name = 'root'
    
    with ec.ExpManager() as manager:        # Generate a manager of this custom type
        instReqQ = manager.Queue()          # Set up queues for communicating between processes during runs
        fileReqQ = manager.Queue()
        logQ = manager.Queue(-1)
               
        exp = manager.ExpController()       # Build a custom data storage object within the manager
        
        
        ####### SET UP LOGGING #######
        logqueuehand = logging.handlers.QueueHandler(logQ)
        if not os.path.exists(r'C:/Data/PXCLogs'):
            os.makedirs(r'C:/Data/PXCLogs')
        logpath = 'C:/Data/PXCLogs/PxcSession_{:s}.log'.format(dt.strftime(dt.now(),'%Y-%m-%d_%H-%M-%S'))
        logfilehand = logging.FileHandler(logpath, mode='w+')
        logconhand = logging.StreamHandler()
        logfilehand.setLevel(logging.DEBUG)
        logqueuehand.setLevel(logging.DEBUG)
        logconhand.setLevel(logging.WARNING)
        recfmt = logging.Formatter('%(asctime)s\t %(name)-8s %(levelname)-8s %(processName)-8s %(message)s')
        metafmt = logging.Formatter('%####\t%(message)-50s####')
        confmt = logging.Formatter('%(message)s')
        logfilehand.setFormatter(recfmt)
        logconhand.setFormatter(confmt)
        
        listener = lh.PXCLogger(logQ, (logfilehand, logconhand))
        listener.start()        
        
        logroot = logging.getLogger('root')
        logroot.addHandler(logqueuehand)
        logmeta = logging.getLogger('meta')
        logmeta.addHandler(logqueuehand)
        
        logmeta.critical('Python Experiment Controller Code')        
        logmeta.critical('Written by J.A.W. Straquadine')
        logmeta.critical('')
        logmeta.critical('Session Started %s' % dt.strftime(dt.today(), '%y-%m-%d, %H:%M:%S'))
        logmeta.critical('')
        logmeta.critical('\t------ V E R S I O N S ------')
        logmeta.critical('*\tPXC:\t\tv%s' % exp.get_version())
        logmeta.critical('*\tpython:\t\tv%s.%s.%s' % sys.version_info[:3])
        logmeta.critical('*\tmatplotlib:\t\tv%s' % matplotlib.__version__)
        logmeta.critical('*\tpyvisa:\t\tv%s' % pyvisa.__version__)
        logmeta.critical('')
        logmeta.critical('\t------ C O M P U T E R ------')
        logmeta.critical('*\tComputer:\t%s' % platform.node())
        logmeta.critical('*\tPlatform:\t%s' % platform.platform())
        logmeta.critical('*\tProcessor:\t%s' % platform.processor())
        logmeta.critical('*\tCores:\t%d' % mp.cpu_count())
        logmeta.critical('')
                
       # START YOUR ENGINES
                
        gui = eg.ExpGUI(exp, instReqQ, fileReqQ, logQ)  # Build the GUI        
        gui.startGUI()

        listener.stop()
        logging.shutdown()