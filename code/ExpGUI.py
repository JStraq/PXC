import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as tkm
import InstHandlers as ih
import FileHandlers as fh
import time
import re
import matplotlib
import os
import numpy as np
import HelperFunctions as hf
import commands as sc
import multiprocessing as mp
import Apparatus as ap
import logging

matplotlib.use("TkAgg")
import Plotter as plt

class ExpGUI:
    """ Contains the general framework of the control panel itself, and
        provides all the general functions for the buttons.
        All user-facing execution starts here.
        
        Parameters
        ----------
        exp : ExpController
            overarching object to enable communication between parallel \
            processes during the run.
        instReqQ : multiprocessing.Queue
            Queue for requesting data or action from the instrumentation
            process
        fileReqQ : multiprocessing.Queue
            Queue for requesting data or action from the file process
        logQ : multiprocessing.Queue
            Queue for sending event records to logs.
    """
    
    def __init__(self, exp, instReqQ, fileReqQ, logQ):
        self.exp = exp
        self.instReqQ = instReqQ
        self.fileReqQ = fileReqQ
        self.logQ = logQ
        self.logger = logging.getLogger('gui')        
        self.logger.addHandler(logging.handlers.QueueHandler(logQ))
        self.logger.setLevel(logging.DEBUG)
        
        self.root = tk.Tk()
        self.insertType = None
        self.seqFileName = None
        self.app = ap.Apparatus(self.exp, logQ)

        self.root.report_callback_exception = self.logError

        # # Plot settings

        self.monInsts = []
        self.monParams = []
        self.monVals = []
        self.subMonButtons = []
        self.monInstBoxes = []
        self.monParamBoxes = []
        self.monValLabels = []
        self.monUnits = []
        self.monInstTraces = []
        self.monParamTraces = []
        self.monHeaders = []

        self.drawGUI(self.root)
        

    def logError(self, exception, value, traceback):
        """
        Pass any errors into the log file to make sure they get saved
        """        
        self.logger.exception(exception)


    def drawGUI(self, master):
        """ 
        Actually build the window itself, and dictate which widget goes where
        and what each button does.
        The GUI is built in a series of frames, which help to keep this
        code and the layout itself more organized.
            
        Parameters
        ----------
        master : tk.root
            The base window into which everything will be populated
        """
        # SET UP THE FRAMES FOR EVERYTHING TO SIT IN
        self.pad = 10  # space between frames
        self.master = master
        self.master.wm_title('PXC, v{:s}'.format(self.exp.get_version()))
        self.master.attributes("-topmost", True)
        self.master.attributes("-topmost", False)
        self.root.protocol("WM_DELETE_WINDOW", self.confirm_quit)
        self.frameUser = tk.Frame(self.master, height=50, width=800)
        self.frameUser.grid(row=0, column=0, columnspan=3, sticky='EW', padx=self.pad, pady=self.pad)
        self.frameExp = tk.Frame(self.master, height=500, width=200)
        self.frameExp.grid(row=1, column=0, sticky='NSEW', padx=self.pad, pady=self.pad)
        self.framePlt = plt.PlotManager(self.master, 1, 1, self.exp, self.fileReqQ)
        self.frameSeq = tk.Frame(self.master, height=500, width=200)
        self.frameSeq.grid(row=1, column=2, sticky='NSEW', padx=self.pad, pady=self.pad)

        self.framePlt.plotbook.bind('<Double-1>', lambda args: self.framePlt.changePlotSettings())

        ## CONTROL HOW THEY SCALE WITH THE WINDOW
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=4)
        self.master.grid_columnconfigure(2, weight=1)
        self.master.grid_rowconfigure(0, weight=0)
        self.master.grid_rowconfigure(1, weight=1)

        # FIRST FRAME: USER INFORMATION, RUNS ALONG TOP
        ## Labels
        tk.Label(self.frameUser, text="User").grid(row=0, column=0, sticky='NSEW')
        tk.Label(self.frameUser, text="Project").grid(row=0, column=1, sticky='NSEW')
        tk.Label(self.frameUser, text="Sample").grid(row=0, column=2, sticky='NSEW')
        tk.Label(self.frameUser, text="Comment").grid(row=0, column=3, columnspan=2, sticky='NSEW')
        tk.Label(self.frameUser, text="Path:").grid(row=2, column=0, sticky='E')

        ## Text entry widgets

        self.user = tk.StringVar()
        self.project = tk.StringVar()
        self.sample = tk.StringVar()
        self.userBox = tk.Entry(self.frameUser, textvariable=self.user)
        self.userBox.grid(row=1, column=0, sticky='NSEW', padx=2, pady=2)
        self.projectBox = tk.Entry(self.frameUser, textvariable=self.project)
        self.projectBox.grid(row=1, column=1, sticky='NSEW', padx=2, pady=2)
        self.sampleBox = tk.Entry(self.frameUser, textvariable=self.sample)
        self.sampleBox.grid(row=1, column=2, sticky='NSEW', padx=2, pady=2)
        self.comment = tk.Text(self.frameUser, height=2, width=15)
        self.comment.grid(row=1, column=3, rowspan=2, columnspan=2, sticky='NSEW', padx=2, pady=2)
        self.path = tk.Entry(self.frameUser)
        self.path.grid(row=2, column=1, columnspan=2, sticky='NSEW', padx=2, pady=2)

        #### TESTING PURPOSES ##########
        self.user.set('Josh')
        self.project.set('tests')
        self.sample.set('001')
        ################################

        # Control scaling
        self.frameUser.grid_columnconfigure(0, weight=0)
        self.frameUser.grid_columnconfigure(1, weight=0)
        self.frameUser.grid_columnconfigure(2, weight=0)
        self.frameUser.grid_columnconfigure(3, weight=4)

        # SECOND FRAME: EXPERIMENT INFORMATION
        ## Labels
        tk.Label(self.frameExp, text="Active Instruments").grid(row=0, column=1, sticky='NSEW')

        ## Experiment definition widgets
        self.buildButton = tk.Button(self.frameExp, text='Edit Instruments', command=self.buildExperiment)
        self.buildButton.grid(column=0, row=0, sticky='NSEW', padx=5, columnspan=4)
        self.activeListBox = tk.Listbox(self.frameExp, height=10, width=45)
        self.activeListBox.grid(column=0, row=1, sticky='NSEW', pady=10, padx=5, columnspan=4)

#        monspacing = 10

        self.statusFrame = tk.Frame(self.frameExp, relief=tk.RIDGE, borderwidth=1)
        self.statusFrame.grid(row=2, column=0, columnspan=3, sticky='NSEW', padx=10, pady=10)
        self.status = [tk.Label(self.statusFrame, text='') for x in range(4)]
        for ii in range(len(self.status)):
            self.status[ii].grid(row=ii, column=0, columnspan=4, pady=0, sticky='NSW')
        self.updateStatus()
        self.addMonButton = tk.Button(self.frameExp, text='...', command=self.addMonitor, width=45)
        #self.addMonButton.grid(row=4, column=0, columnspan=4, sticky='NSEW')
        self.frameExp.grid_columnconfigure(0, weight=1)
        self.frameExp.grid_columnconfigure(1, weight=1)
        self.frameExp.grid_columnconfigure(2, weight=1)


        # FIFTH FRAME: SEQUENCE EDITING AND CONTROL, RUNS DOWN RIGHT SIDE
        ## Labels
        tk.Label(self.frameSeq, text="Sequence Controls").grid(row=0, column=0, columnspan=2, sticky='NSEW')
        tk.Label(self.frameSeq, text="Active Sequence").grid(row=5, column=0, columnspan=2, sticky='NSEW')

        ## Sequence buttons and widgets
        self.runSeqButton = tk.Button(self.frameSeq, text='Run Sequence', command=self.runSequence)
        self.runSeqButton.grid(column=0, row=1, sticky='NSEW', padx=5)
        self.enableButton = tk.Button(self.frameSeq, text='Enable Selected', command=self.enableSteps)
        self.enableButton.grid(column=0, row=2, sticky='NSEW', padx=5)
        self.disableButton = tk.Button(self.frameSeq, text='Disable Selected', command=self.disableSteps)
        self.disableButton.grid(column=0, row=3, sticky='NSEW', padx=5)
        self.abortSeqButton = tk.Button(self.frameSeq, text='Abort Sequence', command=self.abortSequence)
        self.abortSeqButton.grid(column=0, row=4, sticky='NSEW', padx=5, columnspan=2)
        self.insertSeqButton = tk.Button(self.frameSeq, text='Insert Step', command=self.insertSeqStep)
        self.insertSeqButton.grid(column=1, row=1, sticky='NSEW', padx=5)
        self.dupSeqButton = tk.Button(self.frameSeq, text='Duplicate Selected', command=self.dupSeqStep)
        self.dupSeqButton.grid(column=1, row=2, sticky='NSEW', padx=5)
        self.delSeqButton = tk.Button(self.frameSeq, text='Delete Selected', command=self.delSeqStep)
        self.delSeqButton.grid(column=1, row=3, sticky='NSEW', padx=5)
        self.sequenceList = tk.Listbox(self.frameSeq, selectmode='extended', height=30)
        self.sequenceList.grid(column=0, row=6, columnspan=2, sticky='NSEW')
        self.sequenceList.bind('<Double-1>', self.editSeqStep)
        self.loadSeqButton = tk.Button(self.frameSeq, text='Load Sequence', command=self.loadSeqFile)
        self.loadSeqButton.grid(column=0, row=7, sticky='NSEW', padx=5)
        self.saveSeqButton = tk.Button(self.frameSeq, text='Save Sequence', command=self.saveSeqFile)
        self.saveSeqButton.grid(column=1, row=7, sticky='NSEW', padx=5)
        self.moveUpButton = tk.Button(self.frameSeq, text='Move Up', command=self.moveSeqUp)
        self.moveUpButton.grid(column=0, row=8, sticky='NSEW', padx=5)
        self.moveDownButton = tk.Button(self.frameSeq, text='Move Down', command=self.moveSeqDown)
        self.moveDownButton.grid(column=1, row=8, sticky='NSEW', padx=5)
        ## Control scaling
        self.frameSeq.grid_columnconfigure(0, weight=1)
        self.frameSeq.grid_columnconfigure(1, weight=1)
        for x in range(8):
            self.frameSeq.grid_rowconfigure(x, weight=0)
        self.frameSeq.grid_rowconfigure(6, weight=1)
        
        self.logger.info('Finished Building GUI')


    def startGUI(self):
        """ 
        Starts the loop which handles all GUI input and output.
        Also handles the end condition when the GUI mainloop exits.
        """
        self.logger.info('GUI init')
        tk.mainloop()  # This is where the GUI itself runs: the mainloop handles all events
        
        self.logger.info('GUI exit')
        self.exp.kill() # once the GUI closes, trigger destruction of other processes
        self.app.rm.close()
        
        
    def buildExperiment(self):
        """
        Opens a dialog for activating and assigning names to devices
        While this is a bit clunky, the idea is that it forces you to think
        about which device is which to prevent confusion later.
        These labels end up in the column headers.
        """
        # Set up the popup window
        self.logger.info('Open the BuildExperimentDialog')
        top = tk.Toplevel()
        top.protocol("WM_DELETE_WINDOW", lambda: self.cancelBuildExp(top))
        top.minsize(width=600, height=300)
        top.focus_force()
        top.grab_set()
        top.wm_title('Build Experiment')

        instName = tk.StringVar()
        instName.set('')  # TEMPORARY

        # choosing the instruments
        tk.Label(top, text='Available Instruments').grid(row=0, column=0, sticky='NSEW')
        top.availListBox = tk.Listbox(top, height=5, selectmode=tk.SINGLE, exportselection = 0)
        top.availListBox.grid(row=1, column=0, rowspan=3, sticky='NSEW')
        top.activeListBox = tk.Listbox(top, height=5, selectmode=tk.SINGLE)
        top.activeListBox.grid(row=1, column=3, rowspan=3, sticky='NSEW')

        tk.Label(top, text='Name:').grid(row=0, column=1, columnspan=2, sticky='NSEW')
        top.namebox = tk.Entry(top, textvariable=instName)
        top.namebox.grid(row=1, column=1, columnspan=2, sticky='NSEW', padx=5)

        tk.Label(top, text='Active Instruments').grid(row=0, column=3, sticky='NSEW')
        top.instToolTip = tk.Label(top, text='', fg='red')
        top.instToolTip.grid(row=3, column=1, columnspan=2, sticky='NSEW')
        top.subInst = tk.Button(top, text='<<', command=lambda: self.deactivateInstr(top))
        top.subInst.grid(row=2, column=1, sticky='NSEW', pady=5)
        top.addInst = tk.Button(top, text='>>', command=lambda: self.activateInstr(top))
        top.addInst.grid(row=2, column=2, sticky='NSEW', pady=5)

        # control buttons
        top.refreshInstr = tk.Button(top, text='Refresh', command=lambda: self.refreshBuildExp(top))
        top.refreshInstr.grid(row=4, column=0, sticky='NSEW')
        top.applyInstr = tk.Button(top, text='Apply Changes', command=lambda: self.applyBuildExp(top))
        top.applyInstr.grid(row=4, column=1, columnspan=2, sticky='NSEW')
        top.cancelInstr = tk.Button(top, text='Cancel', command=lambda: self.cancelBuildExp(top))
        top.cancelInstr.grid(row=4, column=3, sticky='NSEW')

        top.grid_columnconfigure(0, weight=2)
        top.grid_columnconfigure(1, weight=1)
        top.grid_columnconfigure(2, weight=1)
        top.grid_columnconfigure(3, weight=2)
        top.grid_rowconfigure(0, weight=0)
        top.grid_rowconfigure(1, weight=0)
        top.grid_rowconfigure(2, weight=0)
        top.grid_rowconfigure(3, weight=1)
        top.grid_rowconfigure(4, weight=0)

        # Gather the available instruments from VISA, sort into available
        hf.centerWindow(top)
        self.refreshBuildExp(top)
        

    def refreshBuildExp(self, top):
        """
        Perform a VISA refresh on the apparatus, then push changes to the BuildExp GUI dialog
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        """
        self.logger.info('Refreshing the BuildExperiment dialog')
        self.app.findInstruments()
        
        top.activeListBox.delete(0, tk.END)
        top.availListBox.delete(0, tk.END)
        newAvail = self.app.get_availInsts()
        newActive = self.app.get_activeInsts()

        # sort them by address
        nums = [int(str(x).split(':')[0]) for x in newAvail]
        order = np.argsort(nums)

        for ii in order:  # replace with new
            instr = newAvail[ii]
            top.availListBox.insert(tk.END, str(instr))
        for instr in newActive:  # replace with new
            top.activeListBox.insert(tk.END, str(instr))


    def activateInstr(self, top):
        """
        Check existence/uniqueness of the name, then move the instrument
        to the active list and assign the new name.
        
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        """
        if (len(top.availListBox.curselection()) != 0):  # if something in availListBox is selected
            if (top.namebox.get() != ''):  # and the name string box isn't empty
                if top.namebox.get() not in [top.activeListBox.get(x).split(':')[0] for x in
                                             range(top.activeListBox.size())]:  # and the name is not a duplicate
                    instr = top.availListBox.get(tk.ACTIVE)
                    self.logger.info('Trying to activate an instrument, {:s}'.format(instr))
                    top.availListBox.delete(tk.ACTIVE)  # remove from gui available box
                    top.activeListBox.insert(tk.END, '{:s}:{:s}'.format(top.namebox.get(),
                                                                        str(instr)))  # add it to the gui active box
                    self.logger.info('Success, instrument {:s} activated'.format(top.activeListBox.get(tk.END)))
                    top.instToolTip.config(text='')  # stop yelling at user, they did ok.
                    top.namebox.delete(0, tk.END)

                    # re-sort them by address
                    newActive = top.activeListBox.get(0, tk.END)
                    top.activeListBox.delete(0, tk.END)
                    for instr in sorted(newActive):  # replace with new
                        top.activeListBox.insert(tk.END, str(instr))

                else:
                    self.logger.info('Failed, name is a duplicate')
                    top.instToolTip.config(text='name already taken')  # yell at user for doing it wrong
            else:
                self.logger.info('Failed, no name given')
                top.instToolTip.config(text='must provide name')  # with scary red text


    def deactivateInstr(self, top):
        """
        Remove the selected instrument from the active list
        
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        """
        if len(top.activeListBox.curselection()) != 0:  # if something in activeListBox is selected
            instr = top.activeListBox.get(tk.ACTIVE)
            self.logger.info('Deactivate an instrument, {:s}'.format(instr))
            name = instr.split(':')
            top.activeListBox.delete(tk.ACTIVE)  # delete it from the gui "active" listbox
            top.availListBox.insert(tk.END, '{:s}:{:s}'.format(name[1], name[2]))  # put it back

            # re-sort them by address
            newAvail = top.availListBox.get(0, tk.END)
            nums = [float(x.split(':')[0]) for x in newAvail]
            order = np.argsort(nums)
            top.availListBox.delete(0, tk.END)

            for ii in order:  # replace with new
                instr = newAvail[ii]
                top.availListBox.insert(tk.END, str(instr))


    def applyBuildExp(self, top):
        """
        Push the current instrument configuration to the rest of the program/gui,
        then close the dialog
        
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        """
        
        insts = self.app.instList
        self.logger.info('Pushing BuildExp changes to main GUI')
        self.logger.info('Instruments:')
        strings = [x.split(':',1)[1] for x in top.activeListBox.get(0, tk.END)]
        
        for inst in insts:
            self.logger.info('\t'+str(inst))
            inst.clearName()
            if str(inst) not in top.availListBox.get(0, tk.END):
                names = [x.split(':')[0] for x in top.activeListBox.get(0, tk.END)]
                index = strings.index(str(inst))
                inst.setName(names[index])
        
        self.app.updateInsts(insts)
           
        self.activeListBox.delete(0, tk.END)
        for inst in self.app.get_activeInsts():
            self.activeListBox.insert(tk.END, str(inst))
        top.grab_release()
        top.destroy()  # close this dialog



    def cancelBuildExp(self, top):
        """
        Abort all changes and close the dialog.
        
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        """
        self.logger.info('Canceling BuildExp')
        top.grab_release()
        top.destroy()


    def refreshInstruments(self):
        """
        Check the list of connected instruments and bring it up to date
        """
        self.logger.info('Refreshing the instrument lists')
        activeInsts = []
        for inst in self.app.instList:
            if inst.name is not None:
                activeInsts.append(str(inst))
        self.activeListBox.delete(0, tk.END)
        for ai in activeInsts:
            self.activeListBox.insert(tk.END, ai)


    def updateStatus(self):
        """
        Read the status indicators from the ``ExpController``
        """
        es = self.exp.getStatus()
        for ii in range(len(self.status)):
            self.status[ii]['text'] = es[ii]



    # SEQUENCE FUNCTIONS -----------------------------------------

    def insertSeqStep(self):
        """
        Create a new sequence step, first by opening a box for the user
        to choose what type, then creating that object in the apparatus sequence.
        """
        self.logger.info('Inserting a new sequence step')
        self.insertType = None
        self.chooseStepType()  # open the step type selection window
        self.logger.info('Selected InsertType {:s}'.format(str(self.insertType)))
        if self.insertType is not None:
            position = 0
            if len(self.sequenceList.curselection()) == 0:
                position = self.sequenceList.size()
            else:
                position = self.sequenceList.curselection()[0]
            newStep = self.insertType(exp=self.exp, app=self.app, pos=position, gui=self)  # this runs the constructor for the new seq step
            self.app.appendSequence(newStep, position)
            if isinstance(newStep, sc.LoopCmd):
                self.app.appendSequence(sc.LoopEnd(exp=self.exp, app=self.app, pos=position+1, gui=self, loop=newStep), position+1)
            self.updateSequence()
            
        self.master.lift()
        self.master.focus_force()
        

    def chooseStepType(self):
        """
        Sets up the GUI dialog used to select the sequence command type
        """
    
        if len(self.activeListBox.get(0, tk.END)) == 0:
            tkm.showerror(title='Nope', message="No active instruments!")
            return
        else:
            self.logger.info('Selecting step type')
            top = tk.Toplevel()
            hf.centerWindow(top)
            top.grab_set()

            # build all the buttons with the proper commands
            top.minsize(width=100, height=100)
            top.wm_title('Add Sequence Step')
            
            # Generates all the buttons based on the subclasses in the "commands" folder.
            # Pressing the button stores the proper type, so that "insertSeqStep" knows how to make it.
            cmdclasses = sc.SeqCommand.SeqCmd.__subclasses__()
            cmdnames = [x.__name__ for x in cmdclasses]
            cmdorder = np.argsort(cmdnames)
            cmdclasses = [cmdclasses[ii] for ii in cmdorder]
            for ii, subclass in enumerate(cmdclasses): #loops through all existing/registered command types
                if subclass is not sc.LoopEnd:
                    tk.Button(top, text=subclass.cmdname,
                          command=lambda x=subclass: self.setInsertType(top, x)).grid(column=0, row=ii, sticky='NSEW', padx=5)

            tk.Button(top, text='Cancel', command=lambda: self.setInsertType(top, None)).grid(column=0, row=ii+1,
                                                                                              sticky='NSEW', padx=5)
            self.root.wait_window(top)


    def setInsertType(self, top, insertType):
        """
        This function runs when the user clicks one of the buttons on the 
        selection dialog.  It sets the ``self.insertType`` flag to the
        proper type so that the object can be created
        
        Parameters
        ----------
        top : tk.toplevel
            The instrument select dialog box
        insertType : subclass of ``SeqCmd``
            What type to set when this button is pressed
        """        
        # when the user picks an item to insert,
        self.logger.info('Setting insertType')
        self.insertType = insertType  # store it
        top.grab_release()
        top.destroy()  # and close the dialog


    def updateSequence(self):
        """
        Grab any changes to the sequence from the apparatus and make
        sure the GUI is accurate
        """
        self.logger.info('Updating sequence to GUI')
        self.app.updateTitles()
        self.sequenceList.delete(0, tk.END)
        newSequence = self.app.sequence
        enabled = self.app.getSeqEnabled()
        for seqStep in newSequence:
            self.sequenceList.insert(tk.END, seqStep)
        for ii, en in enumerate(enabled):
            if not en:
                self.sequenceList.itemconfig(ii, {'fg': 'gray'})
                
                
    def runSequence(self): 
        """
        Reconfigure the GUI to enable or disable appropriate features,
        then start the child processes for parallelized remote communication
        and file reading/writing.  The main process continues to handle GUI
        updates, plotting, and logging.
        """
        
        # each command stores all its actions, the ExpController just stores the steps.
        if (self.user.get() == '') or (self.project.get() == '') or (self.sample.get() == ''):
            tkm.showwarning('Nope', "Tell me what you're running so I can put it in the right folder!")
        elif self.sequenceList.size() == 0:
            tkm.showwarning('Nope', 'Uh...what sequence?')
        else:
            self.logger.info('Starting Sequence Run')
            self.exp.runSeq()
            self.runSeqButton['state'] = 'disabled'  # disable the sequence buttons to prevent shenanigans
            self.insertSeqButton['state'] = 'disabled'
            self.disableButton['state'] = 'disabled'
            self.enableButton['state'] = 'disabled'
            self.delSeqButton['state'] = 'disabled'
            self.dupSeqButton['state'] = 'disabled'
            self.moveUpButton['state'] = 'disabled'
            self.moveDownButton['state'] = 'disabled'
            self.loadSeqButton['state'] = 'disabled'
            self.saveSeqButton['state'] = 'disabled'
            self.buildButton['state'] = 'disabled'
            self.abortSeqButton['state'] = 'normal'  # start the getaway car

            dataDir = r'C:/Data/{:s}/{:s}/{:s}/'.format(self.user.get(),
                                                       self.project.get(),
                                                       self.sample.get())

            if not os.path.exists(dataDir):
                os.makedirs(dataDir)
            filename = r'{:s}_{:s}_{:s}.dat'.format(self.project.get(), self.sample.get(),
                                                        time.strftime("%Y-%m-%d_%H-%M-%S"))
            self.writeMeta(dataDir, filename)
            filename = dataDir+filename
            self.path.delete(0, tk.END)
            self.path.insert(0, filename)
                                                        
            # Set up the instrument communication process
            appcopy = self.app.serialize()
            instproc = mp.Process(target=ih.instHandler, args=[self.exp, self.instReqQ, self.fileReqQ, self.logQ, appcopy])
            instproc.name = 'inst'
            instproc.start()

            # Set up the file reading and writing process
            self.exp.openFile()
            fileproc = mp.Process(target=fh.fileHandler, args=[(self.exp, self.fileReqQ, self.logQ)])
            fileproc.name = 'file'
            fileproc.start()

            self.framePlt.plotfile = filename
            self.framePlt.clearPlots()

            self.monHeaders = self.app.getVarsList()
            
            self.logger.critical('sequence headers: {:s}'.format('\t'.join(self.monHeaders)))
            if len(self.monHeaders)>1:
                self.logger.critical('requested creation of new file {:s}'.format(filename))
                self.fileReqQ.put(fh.fileRequest('New File', args=(filename, self.monHeaders)))
                self.framePlt.availQuants = self.monHeaders
            self.instReqQ.put(ih.instRequest('Run Sequence', args=()))  # starts running the commands to GPIB

            self.sequenceWatcher()  # instigate the watchdog


    def writeMeta(self, dataDir, filename):
        """
        Write all of the current settings to a metadata file.  This is run
        every time the user starts a sequnce.
        
        Parameters
        ----------
        dataDir : str
            Where to save the data
        filename : str
            What to call the data
        """
        self.logger.info('Opening Meta file')
        metaDir = dataDir + 'meta/'
        if not os.path.exists(metaDir):
            os.makedirs(metaDir)
        filemeta = filename[:-4] + '.meta'

        with open(metaDir+filemeta, 'w+') as f:
            f.write('Pxc v{:s} metadata file\n'.format(self.exp.get_version()))
            f.write('Run: {:s}\n'.format(dataDir+filename))
            f.write('User: {:s}\n'.format(self.user.get()))
            f.write('Project: {:s}\n'.format(self.project.get()))
            f.write('Sample: {:s}\n'.format(self.sample.get()))
            f.write('Comment: {:s}\n'.format(self.comment.get("1.0",tk.END)))
            f.write('\n')
            f.write(self.app.serialize().replace('COMMANDS:', '\nCOMMANDS:'))



    def sequenceWatcher(self):
        """
        This function runs periodically during the sequence to make sure
        all of the changes are updated.  It also detects when the sequence
        is complete, and it reinitializes the GUI back to the noral state.
        """
        if not self.exp.isRunning():
            self.logger.info('Run detected as complete')
            self.runSeqButton['state'] = 'normal'
            self.insertSeqButton['state'] = 'normal'
            self.disableButton['state'] = 'normal'
            self.enableButton['state'] = 'normal'
            self.delSeqButton['state'] = 'normal'
            self.dupSeqButton['state'] = 'normal'
            self.moveUpButton['state'] = 'normal'
            self.moveDownButton['state'] = 'normal'
            self.loadSeqButton['state'] = 'normal'
            self.saveSeqButton['state'] = 'normal'
            self.buildButton['state'] = 'normal'
            self.abortSeqButton['state'] = 'disabled'

            self.exp.endSeq()
            self.updateStatus()

            return None
        else:
            self.updateStatus()

            self.updatePlot()
            self.root.after(500, self.sequenceWatcher)  # update the gui every 500 ms


    def editSeqStep(self, event):
        """
        If you double-click on a step in the list, open its 'edit' dialog
        
        Parameters : event
            unused, but passed in by tk binding anyway
        """
        self.logger.info('Editing sequence step:')
        if len(self.app.sequence)>0:
            if len(self.activeListBox.get(0,tk.END)) != 0:  # only edit if at least SOMETHING is active.
                ii = self.sequenceList.curselection()[0]

                self.app.sequence[ii].edit(running=self.exp.isRunning())
                self.app.updateTitles()
                self.logger.info('\t' + str(self.app.sequence[ii]))

                self.updateSequence()
            else:
                tkm.showerror('Nope', 'No active instruments!')


    def delSeqStep(self):
        """
        deletes all selected elements from the list
        """
        indices = list(self.sequenceList.curselection())
        self.app.deleteSteps(indices)
        self.app.updateTitles()
        self.updateSequence()
        

    def sendInstRequest(self, reqname, arguments):
        """
        adds a single request to the queue, blocks until it's processed
        
        Parameters
        ----------
        reqname : str
            Type of request to be made
        arguments : tuple
            Any necessary data to send along with this request
            
        Returns
        -------
        self.ns.instAns : str
            The response from the instrument process
        """
        request = ih.instRequest(reqname, args=arguments)
        self.instReqQ.put(request)
        self.instReqQ.join()
        return self.ns.instAns


    def dupSeqStep(self):
        """
        duplicates all selected elements in the list, keeping them in order when adjacent
        """
        indices = list(self.sequenceList.curselection()[::-1])
        indices = sorted(indices)

        for ii in indices:
            if isinstance(self.app.sequence[ii], sc.LoopCmd):  # if it's a loop, find its end
                for jj, cmd in enumerate(self.app.sequence):
                    if isinstance(cmd, sc.LoopEnd):
                        if cmd.loop == self.app.sequence[ii]:
                            if jj not in indices:
                                indices.append(jj)
            elif isinstance(self.app.sequence[ii], sc.LoopEnd):  # if it's an end, find its loop
                jj = self.app.sequence.index(self.app.sequence[ii].loop)
                if jj not in indices:
                    indices.append(jj)
                    
        newindices = indices[:]
        space = [indices[ii+1] - indices[ii] for ii in range(len(indices) - 1)]  # space between selected objects
        for ii in range(1, len(indices))[::-1]:  # loop through spaces
            if space[ii - 1] == 1:  # if they're adjacent,
                newindices[ii-1] = newindices[ii]  #

        dups = [self.app.sequence[ii].copy() for ii in indices]  # make duplicate objects
        copied = [self.app.sequence[ii] for ii in indices]

        for ii, cmd in enumerate(dups):  # reattach loop ends to the new copies
            if isinstance(cmd, sc.LoopEnd):
                cmd.loop = dups[copied.index(self.app.sequence[indices[ii]].loop)]

        for ii in range(len(indices))[::-1]:
            self.app.sequence.insert(newindices[ii] + 1, dups[ii])
        
        self.app.protectLoops()
        self.updateSequence()



    def moveSeqUp(self):
        """
        moves all selected items up one item, maintaining order when adjacent items are selected
        """
        indices = list(self.sequenceList.curselection())

        selected = []
        for ii in indices:
            selected.append(self.app.sequence[ii])     # store the commands to be moved
            
        for ii in range(len(indices)):
            if indices[ii] == ii:  # if it can't be moved up, don't move it up!
                del indices[ii]
                   
        for ii in indices:
            cmd = self.app.sequence[ii]
            del self.app.sequence[ii]  # do the moving
            self.app.sequence.insert(ii - 1, cmd)

        self.app.protectLoops()
        
        newIndices = []
        for cmd in selected:
            newIndices.append(self.app.sequence.index(cmd))

        self.updateSequence()
        
        for ii in newIndices:
            self.sequenceList.selection_set(ii)


    def moveSeqDown(self):
        """
        moves all selected items down
        """
        indices = list(self.sequenceList.curselection())

        selected = []
        for ii in indices:
            selected.append(self.app.sequence[ii])     # store the commands to be moved
        
        length = len(self.app.sequence)
        indices = [length-ii-1 for ii in indices]
        indices = indices[::-1]
        for ii in range(len(indices))[::-1]:
            if indices[ii] == ii:  # if it can't be moved down, don't move it down!
                del indices[ii]
        indices = [length-ii-1 for ii in indices]            
        length = len(self.app.sequence)
        
        for ii in indices:
            cmd = self.app.sequence[ii]
            del self.app.sequence[ii]  # do the moving
            self.app.sequence.insert(ii + 1, cmd)

        self.app.protectLoops()
        
        newIndices = []
        for cmd in selected:
            newIndices.append(self.app.sequence.index(cmd))

        self.updateSequence()
        for ii in newIndices:
            self.sequenceList.selection_set(ii)
            
            
    def abortSequence(self):
        """
        Just sets the ``abort`` flag for the ExpController: all three
        processes will see that on their next updates and start exiting.
        """
        self.exp.abort()


    def updatePlot(self, newSettings=False):
        """
        Updates the plots
        
        Parametrs
        ---------
        newsettings : boolean
            whether or not the settings have been changed.  If yes, then a 
            full re-read of the relevant data is required.  If no, then we
            can just append the last few datapoints for a quicker operation.
        TODO: THIS ISN'T IMPLEMENTED YET
        """
        self.framePlt.updatePlots()


    def confirm_quit(self):
        """
        Make sure the user meant to close the GUI
        """
        if tkm.askyesno("Quit?", "Are you sure?"):
            self.master.destroy()
            self.exp.closeFile()
            self.exp.kill()


    def saveSeqFile(self):
        """
        Open the dialog to save a sequence file
        """
        seqFile = tk.filedialog.asksaveasfile(mode='w', defaultextension=".seq")
        if seqFile is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        seqFile.write('Sequence file generated by version {:s}\n'.format(self.exp.get_version()))
        seqFile.write(self.app.serialize())
        seqFile.close()

    def loadSeqFile(self):
        """
        Open the dialog to load a sequence file, reads it, and rebuilds
        the necessary connections.  The user will be forced to map
        the old and new instruments every time, which is unavoidable given
        the inherent flexibility of this scheme.
        """
        # open a file
        seqFile = tk.filedialog.askopenfile(mode='r')
        if seqFile is None:
            return

        # Get the list of required instruments from the file
        line = ''
        while line != 'INSTRUMENTS:\n':
            line = seqFile.readline()
        self.loadInsts = []
        instsDone = False
        while not instsDone:
            line = seqFile.readline()
            if re.match('COMMANDS', line) is not None:
                instsDone = True
                break
            self.loadInsts.append(line.strip())
        seqFile.seek(0)
        self.loadAppSer = seqFile.readlines()
        seqFile.close()

        requiredInsts = {}
        for inst in self.loadInsts:
            try:
                addr, model, name = inst.strip().split('\t')
                requiredInsts[addr] = (model, name)
            except ValueError:
                pass

        # Compare the lists: are there enough pieces of equipment hooked up to do this?
        reqModelCounts = {}
        for key in requiredInsts.keys():
            model = requiredInsts[key][0]
            if model not in reqModelCounts.keys():
                reqModelCounts[model] = 0
            reqModelCounts[model] += 1

        availModelCounts = {}
        self.app.findInstruments()
        for inst in self.app.instList:
            if inst.model not in availModelCounts.keys():
                availModelCounts[inst.model] = 0
            availModelCounts[inst.model] += 1

        loadOK = True
        for key in reqModelCounts.keys():
            if key not in availModelCounts.keys():
                loadOK = False
                break
            else:
                if availModelCounts[key] < reqModelCounts[key]:
                    loadOK = False
                    break

        if not loadOK:
            loadErrMsg = 'To load that file, you need to connect:\n'
            for key in reqModelCounts.keys():
                loadErrMsg += '{:d} {:s}\n'.format(reqModelCounts[key], key)

            loadErrMsg += "\n\nBut all that's connected is \n"
            for key in availModelCounts.keys():
                loadErrMsg += '{:d} {:s}\n'.format(availModelCounts[key], key)
            tkm.showerror('Nope', message=loadErrMsg)
            return

        # If we've made it here, then all systems are go
        self.window = tk.Toplevel()
        self.window.grab_set()
        self.window.wm_title('Load Sequence')
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW",
                             self.loadMap)  # if they delete the window, assume they liked their settings

        tk.Label(self.window, text='Old File:', width=30).grid(row=0, column=0, sticky='NSEW')
        tk.Label(self.window, text='New Address:', width=30).grid(row=0, column=1, sticky='NSEW')
        tk.Label(self.window, text='New Name:', width=30).grid(row=0, column=2, sticky='NSEW')

        sortByModel = {m:[] for m in reqModelCounts.keys()}
        for addr in requiredInsts.keys():
            model = requiredInsts[addr][0]
            name = requiredInsts[addr][1]
            addrnum = re.search('::([0-9]+)::', addr).group(1)
            sortByModel[model].append(('{:s}:{:s}:{:s}'.format(name, addrnum, model),
                                       '{:s}\t{:s}\t{:s}'.format(addr, model, name)))  # get both short and long formats
        print(sortByModel)

        activeByModel = {m:[] for m in reqModelCounts.keys()}
        for inst in self.app.instList:
            activeByModel[inst.model].append(str(inst))

        row=1
        self.comboVars = []
        self.nameVars = []
        self.originals = []

        for m in sortByModel.keys():
            modcount = 0
            for ri in sortByModel[m]:
                short, long = ri
                tk.Label(self.window, text=short).grid(row=row, column=0, sticky='NSEW')
                self.originals.append(ri)
                self.comboVars.append(tk.StringVar())
                self.nameVars.append(tk.StringVar())
                ttk.Combobox(self.window, textvariable=self.comboVars[-1], values=activeByModel[m]).grid(row=row, column=1, sticky='NSEW')
                ttk.Entry(self.window, textvariable=self.nameVars[-1]).grid(row=row, column=2, sticky='NSEW')
                self.nameVars[-1].set(short.split(':')[0])
                self.comboVars[-1].set(sorted(activeByModel[m])[modcount])
                modcount+=1
                row += 1

        hf.centerWindow(self.window)
        self.master.wait_window(self.window)

    
    def loadMap(self):
        """
        Make all of the necessary replacements to map the old sequence
        into the new setup
        """
        newnames = [nv.get() for nv in self.nameVars]
        newaddrnums = [cv.get().split(':')[0] for cv in self.comboVars]
        newaddrs = ['GPIB0::{:s}::INSTR'.format(addrnum) for addrnum in newaddrnums]
        newmodels = [cv.get().split(':')[1] for cv in self.comboVars]

        if len(list(set(newnames))) < len(newnames) or len(list(set(newaddrs))) < len(newaddrs):
            tkm.showerror('Nope', message='Instrument mapping assignments are not unique!', parent=self.window)
        else:
            if tkm.askyesno("Quit?", "Are you sure you like these settings?", parent=self.window):
                self.window.destroy()
              
                replacements = {}
                for ii, (short, long) in enumerate(self.originals):
                    replacements[short] = '{:s}:{:s}:{:s}'.format(newnames[ii], newaddrnums[ii], newmodels[ii])
                    replacements[long] = '{:s}\t{:s}\t{:s}'.format(newaddrs[ii], newmodels[ii], newnames[ii])
                
                placeholders = {}
                for ii, orig in  enumerate(list(replacements.keys())):
                    ph = 'PLACEHOLDER{:06d}'.format(ii)
                    placeholders[ph] = replacements[orig]
                    replacements[orig] = ph
                
                self.loadAppSer = ''.join(self.loadAppSer)
                for key in replacements.keys():
                    self.loadAppSer = self.loadAppSer.replace(key, replacements[key])
                for key in placeholders.keys():
                    self.loadAppSer = self.loadAppSer.replace(key, placeholders[key])

                self.loadAppSer = '\n'.join(self.loadAppSer.split('\n')[1:])
                self.app.deserialize(self.loadAppSer, gui=self)
                self.updateSequence()
                self.refreshInstruments()


    def enableSteps(self):
        """
        Mark all selected steps enabled to run during the next sequence
        """
        indices = self.sequenceList.curselection()
        for ii in indices:  # make sure to treat loops and their ends the same way
            if isinstance(self.app.sequence[ii], sc.LoopCmd):
                for jj, cmd in enumerate(self.app.sequence):
                    if isinstance(cmd, sc.LoopEnd):
                        if cmd.loop == self.app.sequence[ii]:
                            if jj not in indices:
                                indices.append(jj)
                                indices = sorted(indices)
                            break
            if isinstance(self.app.sequence[ii], sc.LoopEnd):
                parentLoopIndex = self.app.sequence.index(self.app.sequence[ii].loop)
                if parentLoopIndex not in indices:
                    indices.append(parentLoopIndex)
                    indices = sorted(indices)
        for ii in indices:
            self.app.sequence[ii].enabled = True
        return None
        self.updateSequence()

        
    def disableSteps(self):
        """
        Mark all selected steps as disabled, will NOT run during the next sequence
        """
        indices = self.sequenceList.curselection()
        for ii in indices:  # make sure to treat loops and their ends the same way
            if isinstance(self.app.sequence[ii], sc.LoopCmd):
                for jj, cmd in enumerate(self.app.sequence):
                    if isinstance(cmd, sc.LoopEnd):
                        if cmd.loop == self.app.sequence[ii]:
                            if jj not in indices:
                                indices.append(jj)
                                indices = sorted(indices)
                            break
            if isinstance(self.app.sequence[ii], sc.LoopEnd):
                parentLoopIndex = self.app.sequence.index(self.app.sequence[ii].loop)
                if parentLoopIndex not in indices:
                    indices.append(parentLoopIndex)
                    indices = sorted(indices)
        for ii in indices:
            self.app.sequence[ii].enabled = False
        self.updateSequence()


    def addMonitor(self):
        """
        Create a new variable monitor on the left hand side of the screen.
        """
        hf.noimp()
#        if 'Timestamp' in self.monHeaders:
#            self.monHeaders.remove('Timestamp')
#        insts = [h.split('--')[0].strip() for h in self.monHeaders]
#        insts = [''] if insts==[] else insts
#        insts = list(set(insts))
#        
#        monCount = len(self.monInsts) + 1
#        self.addMonButton.grid_forget()
#        self.addMonButton.grid(row=4+monCount, column=0, columnspan=4, sticky='NSEW')
#
#        self.subMonButtons.append(tk.Button(self.frameExp, text='X', activeforeground='red',
#                                            command=lambda ii=(monCount-1): self.subMonitor(ii)))
#        self.subMonButtons[-1].grid(row=3+monCount, column=0, sticky='NSEW')
#
#        self.monInsts.append(tk.StringVar())
#        self.monParams.append(tk.StringVar())
#        self.monVals.append(tk.StringVar())
#        self.monInstBoxes.append(ttk.Combobox(self.frameExp, textvariable=self.monInsts[-1], width=15))
#        self.monParamBoxes.append(ttk.Combobox(self.frameExp, textvariable=self.monParams[-1], width=15))
#        self.monValLabels.append(tk.Label(self.frameExp, textvariable=self.monVals[-1], width=15, relief='ridge'))
#        self.monInstBoxes[-1].grid(row=3+monCount, column=1, sticky='NSEW')
#        self.monInstBoxes[-1]['values'] = insts[:]
#        self.monInstBoxes[-1].current(0)
#        self.monParamBoxes[-1].grid(row=3+monCount, column=2, sticky='NSEW')
#        self.monValLabels[-1].grid(row=3+monCount, column=3, sticky='NSEW')
#        self.monInstTraces.append(self.monInsts[-1].trace("w", lambda v,n,m,ii=monCount-1: self.updateMonParams(v,n,m,ii)))
#        self.monParamTraces.append(self.monParams[-1].trace("w", lambda v,n,m,ii=monCount-1: self.updateMonUnits(v,n,m,ii)))
#        
#        self.monInstBoxes[-1]['values'] = insts
#        self.monInstBoxes[-1].current(0)
#
#        if len(self.monInsts) == 1:
#            self.refreshMonitors()

    def subMonitor(self, ii):
        """
        Delete a variable monitor
        
        Pameters
        --------
        ii : int
            The row number of the monitor to be deleted
        """
        hf.noimp()
#        monCount = len(self.monInsts) - 1
#        self.addMonButton.grid_forget()
#        self.addMonButton.grid(row=4+monCount, column=0, columnspan=4, sticky='NSEW')
#        self.subMonButtons[-1].destroy()
#        del self.subMonButtons[-1]
#
#        self.monInsts[ii].trace_vdelete("w", self.monInstTraces[ii])
#        self.monParams[ii].trace_vdelete("w", self.monParamTraces[ii])
#        self.monInstBoxes[ii].destroy()
#        self.monParamBoxes[ii].destroy()
#        self.monValLabels[ii].destroy()
#        del self.monInstBoxes[ii]
#        del self.monInsts[ii]
#        del self.monParamBoxes[ii]
#        del self.monParams[ii]
#        del self.monValLabels[ii]
#        del self.monVals[ii]
#        del self.monInstTraces[ii]
#        del self.monParamTraces[ii]
#        
#        for jj in range(ii, len(self.monInsts)):
#            self.monInstBoxes[jj].grid_forget()
#            self.monParamBoxes[jj].grid_forget()
#            self.monValLabels[jj].grid_forget()
#            self.monInstBoxes[jj].grid(row=4+jj, column=1, sticky='NSEW')
#            self.monParamBoxes[jj].grid(row=4+jj, column=2, sticky='NSEW')
#            self.monValLabels[jj].grid(row=4+jj, column=3, sticky='NSEW')

    def updateMonParams(self, v,n,m, ii):
        """
        Make sure the parameter options match the selected instrument
        
        Parameters
        ----------
        ii : int
            the row to update
        """
        hf.noimp()
#        inst = self.monInsts[ii].get()
#        params = []
#        for head in self.monHeaders:
#            if head.split('--')[0].strip() == inst:
#                try:
#                    param = head.split('--')[1].strip()
#                    params.append(param.split('(')[0].strip())
#                except IndexError:
#                    pass
#        params = [''] if params==[] else params
#        
#        self.monParamBoxes[ii]['values'] = params[:]
#        try:        
#            self.monParamBoxes[ii].current(params.index(self.monParams[ii].get()))
#        except ValueError:
#            self.monParamBoxes[ii].current(0)
#        
#        self.updateMonUnits(None,None,None,ii)
    
    def updateMonUnits(self, v,n,m, ii):
        """
        Make sure the displayed units match the selected parameter
        
        Parameters
        ----------
        ii : int
            the row to update
        """
        hf.noimp()
#        insts = []
#        params = []
#        units = []
#        for ii in range(len(self.monInsts)):
#            insts.append(self.monInsts[ii].get())
#            params.append(self.monParams[ii].get())
#            units.append('')
#            for head in self.monHeaders:
#                head = head.split('(')
#                if len(head)>1:
#                    if head[0].strip() == '{:s}--{:s}'.format(insts[ii], params[ii]):
#                        units[-1] = head[1].strip(' \t\n)')
#                        break
#        self.monUnits = units[:]
    
    def refreshMonitors(self):
        """
        Grab the most recent values of this monitor.
        If a sequence is not running, this causes the apparatus to request
        a measurement of these instruments.  If a sequence IS running, then
        the displayed data will just be the last value which was read.
        (This is intended to avoid having monitor measurements interfere with the sequence.)
        """
        hf.noimp()
#        insts = [x.get() for x in self.monInsts]
#        params = [x.get() for x in self.monParams]
#
#        if self.ns.running:
#            self.fileReqQ.put(fh.fileRequest('Read Latest'))
#            latest = self.ns.fileLatest
#            for ii in range(len(insts)):
#                for key in latest.keys():
#                    if key.split('(')[0].strip() == '{:s}--{:s}'.format(insts[ii], params[ii]):
#                        self.monVals[ii].set('{:s} {:s}'.format(latest[key], self.monUnits[ii]))
#                        break
#            if len(self.monInsts) != 0:
#                self.root.after(1000, self.refreshMonitors)
#            sys.stdout.flush()
#            
#        else:
#            vals = self.sendInstRequest('Read Monitors', args=(insts,params))
#            for ii, val in enumerate(vals):
#                if val is not None:
#                    self.monVals[ii].set('{:s} {:s}'.format(val, self.monUnits[ii]))
#            if len(self.monInsts) != 0:
#                self.root.after(1000, self.refreshMonitors)
