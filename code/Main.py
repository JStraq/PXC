import multiprocessing as mp
import ExpController as ec
import ExpGUI as eg
import logging as lg
import os
from datetime import datetime as dt
import LogHandlers as lh
import importlib
importlib.reload(lg)
#from lib import Apparatus as ap

if __name__ == "__main__":
    
    
    with ec.ExpManager() as manager:        # Generate a manager of this custom type
        instReqQ = manager.Queue()          # Set up queues for communicating between processes during runs
        fileReqQ = manager.Queue()
        logQ = manager.Queue()
        
        exp = manager.ExpController()       # Build a custom data storage object within the manager
        
        
        if not os.path.exists(r'C:/Data/PXCLogs'):
            os.makedirs(r'C:/Data/PXCLogs')
        logpath = 'C:/Data/PXCLogs/PxcSession_{:s}.log'.format(dt.strftime(dt.now(),'%Y-%m-%d_%H-%M-%S'))
        
        logger =  lg.getLogger('pxc_log')
        lg.basicConfig(filename=logpath,
                   filemode='w',
#                   format='%(asctime)s %(levelname)-8s %(message)s',
                   level=lg.INFO,)
#                   datefmt='%Y-%m-%d %H:%M:%S')
        loghand = lh.LogHandler(logpath, logQ)
        logger.addHandler(loghand)
        logger.warning('start log')
        
        
        print('Code Version {:s}'.format(exp.get_version()))
        print('Running on {:d} CPUs'.format(mp.cpu_count()))
        
       # START YOUR ENGINES
        gui = eg.ExpGUI(exp, instReqQ, fileReqQ, logQ)  # Build the GUI        
        logger.warning('start gui')
        gui.startGUI()
        logger.warning('exit gui')
        lg.shutdown()

        
        # app = ap.Apparatus(exp)
        # app.findInstruments()
        # app.instList[0].setName('TempThingy')
        # ser = app.serialize()
        #
        # app2 = ap.Apparatus(exp)
        # app2.deserialize(ser)
        # print(app2.serialize())
        # print(app2.instList[0].params)