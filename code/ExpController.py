import multiprocessing as mp
from multiprocessing.managers import BaseManager
import datetime
from pytz import timezone

class ExpController:
    """
    Stores all of the important shared variables for communicating between the\
    various processes.  This is basically a glorified custom data structure.
    
    Attributes
    ----------
    version : str
        Current version of PXC.
    backup : what?
        what?        
    insertType : todo
        todo
    manager : multiprocessing.Manager
        This object is the primary supervisor of all communications between\
        the various processes once the run begins.  See the documentation for \
        the ``multiprocessing`` module for more details on that.
    q : multiprocessing.Manager.Queue
        A partcular data transfer queue for passing data around.  Again, see\
        the ``multiprocessing`` module docs.
    filepath : str
        filepath of the current file--this is always generated based on the \
        identifying information in the top left corner of the GUI.
    logpath : str
        file where the logs for this session will be stored.  In order \
        to most effectively log all of the various giblets, PXC will generate \
        three different logs, but this one in particular refers to the main \
        process and other events which occur within the GUI between runs.
    log : logging.Logger
        An object for generating log file contents pseudo-automatically.
        See the python builting ``logging`` module docs for more details.
    killFlag : boolean
        Flag for exiting the entire program
    abortFlag : boolean
        Flag for exiting the current run but keeping the program up
    running : boolean
        Keep track of whether or not a sequence is currently running
    fileOpen : boolean
        keeps track of whether or not a file is open
    idle : list of str
        Literal default value for the status indicator
    status0, status1, status2, status3 : str
        The four different components which make up the status indicator
    instAns : str
        stores the most recent response from the instrumentation process
    instBusy : boolean
        Stores whether or not the instrumentation process is currently working
        to prevent bus conflicts/dropped packets
    fileBusy : boolean
        Stores whether or not the file process is currently working
        to prevent bus conflicts/dropped packets
    fileAns : str
        stores the most recent response from the file process
    fileLatest : dict
        stores the most recent data sent from the file process
    unread
    sequence
    logvars
    monitors
    xdata : list
        The 
    ydat
    xparm
    yparam
    linestyle
    gridStatus
    filename : str
        The name of the active file.
    """
    def __init__(self):
        # OVERARCHING INSTANCE VARIABLES
        self.version = '0.7.3x'
        self.backup = None
        self.insertType = None
        self.manager = mp.Manager()
        self.q = self.manager.Queue()
        self.filepath = ''
        
        self.LOCAL_TIMEZONE = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo


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
        
    def getTZ(self):
        return self.LOCAL_TIMEZONE
    
    def isRunning(self):
        return self.running
        
    def isFileOpen(self):
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
        self.abortFlag = True
        self.running = False
    
    def kill(self):
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

    def setStatus(self, status):
        for ii, s in enumerate(status):
            self.status0 = status[0]
            self.status1 = status[1]
            self.status2 = status[2]

    def setStatusLoop(self, status):
        self.status3 = status
        
        
class ExpManager(BaseManager):
    """ Custom data manager for holding on to data and basic functions
        accesible by all of the various processes.
        A "manager" acts as a generic framework for passing data around,
        and we get the freedom to define how that data is stored.
        This class inherits all of its basic structure from 
        ``multiprocessing.managers.BaseManager``, and registers a few 
        custom classes.
    """
    pass
ExpManager.register('ExpController', ExpController)    # Registering these classes means the
ExpManager.register('Queue', mp.JoinableQueue)            # ExpManager can store things of that type