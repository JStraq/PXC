import multiprocessing as mp
import ExpController as ec
import ExpGUI as eg
import logging
import LogHandlers as lh
import importlib
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
        logfilehand = logging.FileHandler('C:/Data/PXCLogs/alog.log', mode='w')
#        logfilehand = lh.LogHandler()
        logconhand = logging.StreamHandler()
        logfilehand.setLevel(logging.DEBUG)
        logqueuehand.setLevel(logging.DEBUG)
        logconhand.setLevel(logging.WARNING)
        recfmt = logging.Formatter('%(asctime)s\t %(name)-8s %(levelname)-8s %(processName)-8s %(message)s')
        metafmt = logging.Formatter('%####\t%(message)-50s####')
        confmt = logging.Formatter('%(message)s')
        logfilehand.setFormatter(recfmt)
        logconhand.setFormatter(confmt)
        
        
#        listener = logging.handlers.QueueListener(logQ, logfilehand)
        listener = lh.PXCLogger(logQ, (logfilehand, logconhand))
        listener.start()        
        
        logroot = logging.getLogger('root')
        logroot.addHandler(logqueuehand)
        logmeta = logging.getLogger('meta')
        logmeta.addHandler(logqueuehand)
        
        logmeta.critical('Code Version %s' % exp.get_version())
        logmeta.critical('Running on %d CPUs' % mp.cpu_count())
        
        
       # START YOUR ENGINES
                
        gui = eg.ExpGUI(exp, instReqQ, fileReqQ, logQ)  # Build the GUI        
        gui.startGUI()

        listener.stop()       
        logging.shutdown()