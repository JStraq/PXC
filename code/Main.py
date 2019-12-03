import multiprocessing as mp
import ExpController as ec
import ExpGUI as eg
#from lib import Apparatus as ap

if __name__ == "__main__":
    with ec.ExpManager() as manager:        # Generate a manager of this custom type
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