import multiprocessing as mp
from multiprocessing.managers import BaseManager

import ExpController as ec
import ExpGUI as eg
#from lib import Apparatus as ap


class ExpManager(BaseManager):
    """ Custom data manager for holding on to data and basic functions
        accesible by all of the various processes.
        A "manager" acts as a generic framework for passing data around,
        and we get the freedom to define how that data is stored.
    """
    pass
ExpManager.register('ExpController', ec.ExpController)    # Registering these classes means the
ExpManager.register('Queue', mp.JoinableQueue)            # ExpManager can store things of that type

#  HERE'S WHERE THE ACTUAL CODE STARTS EXECUTING
if __name__ == "__main__":
    with ExpManager() as manager:           # Generate a manager of this custom type
        exp = manager.ExpController()       # Build a custom data storage object within the manager
        instReqQ = manager.Queue()          # Set up queues for communicating between processes during runs
        fileReqQ = manager.Queue()
               
        print('Code Version {:s}'.format(exp.get_version()))
        print('Running on {:d} CPUs'.format(mp.cpu_count()))
        
       # START YOUR ENGINES
        gui = eg.ExpGUI(exp, instReqQ, fileReqQ)  # Build the GUI

        
        gui.startGUI()

        
        # app = ap.Apparatus(exp)
        # app.findInstruments()
        # app.instList[0].setName('TempThingy')
        # ser = app.serialize()
        #
        # app2 = ap.Apparatus(exp)
        # app2.deserialize(ser)
        # print(app2.serialize())
        # print(app2.instList[0].params)