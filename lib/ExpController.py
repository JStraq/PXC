import multiprocessing as mp
from datetime import datetime as dt
import os
import logging

class ExpController:

    def __init__(self):
        """
        Stores all of the important shared variables for communicating between the various processes
        """
        # OVERARCHING INSTANCE VARIABLES
        self.version = '0.7.3x'
        self.backup = None
        self.insertType = None
        self.manager = mp.Manager()
        self.q = self.manager.Queue()
        self.filepath = ''

        if not os.path.exists(r'C:/Data/PXCLogs'):
            os.makedirs(r'C:/Data/PXCLogs')
        self.logpath = 'C:/Data/PXCLogs/PxcSession_{:s}.log'.format(dt.strftime(dt.now(),'%Y-%m-%d_%H-%M-%S'))
        self.log = logging.getLogger(__name__)

        self.killFlag = False    # for exiting the entire program
        self.abortFlag = False   # for stopping a sequence
        self.running = False
        self.fileOpen = False
        self.idle = ['Status:\tIdle', '', '', '']
        self.status0 = self.idle[0]
        self.status1 = self.idle[1]
        self.status2 = self.idle[2]
        self.status3 = self.idle[3]

        self.instAns = None
        self.instBusy = False
        self.fileBusy = False
        self.fileAns = None
        self.fileLatest = {}
        self.unread = []

        self.sequence = []
        self.logvars = []
        self.monitors = []

        # Plot settings
        self.xdata = []
        self.ydata = []
        self.xparam = None
        self.yparam = None
        self.linestyle = None
        self.gridStatus = False
        self.filename = ''


    def isFileOpen(self):
        self.log.info('New file process started')
        return self.fileOpen

    def openFile(self):
        self.fileOpen = True

    def closeFile(self):
        self.fileOpen = False

    def getLogPath(self):
        return self.logpath

    def get_availInsts(self):
        return self.availInsts
    def set_availInsts(self, new):
        self.availInsts = new
    def get_activeInsts(self):
        return self.activeInsts
    def set_activeInsts(self, new):
        self.activeInsts = new
    def get_allInsts(self):
        return self.availInsts + self.activeInsts
    
    def get_version(self):
        return self.version
    
    def get_fileLatest(self):
        return self.fileLatest

    def set_fileLatest(self, fl):
        self.fileLatest = fl
        
    def get_fileAns(self):
        return self.fileAns
    def set_fileAns(self, fa):
        self.fileAns = fa
        
    def get_instAns(self):
        return self.instAns

    def set_instAns(self, il):
        self.instAns = il
    
    def abort(self):
        self.log.info('AbortFlag set')
        self.abortFlag = True
        self.running = False
    
    def kill(self):
        self.log.info('killFlag set')
        self.abortFlag = True
        self.killFlag = True
    
    def runSeq(self):
        self.abortFlag = False
        self.running = True

    def finish(self):
        self.abortFlag = False
        self.running = False

    def endSeq(self):
        self.running = False
        self.setStatus(self.idle[:])

    def get_killFlag(self):
        return self.killFlag

    def isAborted(self):
        return self.abortFlag

    def getStatus(self):
        return [self.status0, self.status1, self.status2, self.status3]

    def isRunning(self):
        return self.running

    def setStatus(self, status):
        for ii, s in enumerate(status):
            self.status0 = status[0]
            self.status1 = status[1]
            self.status2 = status[2]

    def setStatusLoop(self, status):
        self.status3 = status