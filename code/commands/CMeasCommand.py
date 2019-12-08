import tkinter as tk
from tkinter import ttk
from . import SeqCommand as sc
import FileHandlers as fh
from datetime import datetime
import time
import HelperFunctions as hf
import numpy as np


class CMeasCmd(sc.SeqCmd):
    """
    Repeatedly measure an arbitrary list of parameters.
    This will measure for a certain amount of time or until a condition
    is met, similar to the Wait command.
    
    Parameters
    ----------
    exp : ExpController
        Data/communication manager for the entire setup
    app : Apparatus
        The object storing the sequence of which this command will be part
    pos : int
        Numerical position in the sequence, starting from zero.
    dup : boolean
        Flag for whether or not to open the configuration window:\
        for a brand new sequence command, we need to open it.  If \
        we're just copying an old one, we don't.
    gui : ExpGUI
        A link to the GUI: this is set whenever the sequence is active, \
        and equal to ``None`` if the command is being saved to a `*.seq`.
        
    Attributes
    ----------
    status : list of str
        text to display on the GUI during the execution of this step
    timeout : float
        number of seconds to wait, even if a condition has not been met,\
        the command will not wait longer than this parameter specifies.
    conditionInst : str
        name of the instrument to be polled for the termination condition
    conditionParam : str
        name of the parameter to be polled for the termination condition
    conditionVal : float
        terminate once the parameter reaches this value
    stableTime : float
        Force the parameter to be within +/- the stability for this many seconds
    stability : float
        maximum deviation from ``conditionVal`` for it still to be \
        considered stable
    pollTime : float
        how often (in seconds) to check the condition parameter
    mode : str
        Either ``'Time'`` or ``'Condition'``, describing the termination.
        
    """
    cmdname = 'Continuous Measurement'
    def __init__(self, exp, app, pos, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.status = self.status = ['Status: \tMeasuring', 'Condition:\t', 'Parameter:\t']
        self.type = 'ContinuousMeasurementCommand'
        self.rows = 0
        self.rowheight = 30
        self.wait = 'Time'  # wait for 'Time' or 'Condition'
        self.timeout = 10.0  # how long to wait for each set before proceeding
        self.waitInst = ''
        self.waitParam = ''  # what (if anything) to wait for
        self.stableTime = 10.0  # How long to require stability
        self.stability = 1.0  # Stay less than this value away from the final value for the required time
        self.pollTime = 1.0  # Check the value this often
        self.target = 0.0

        self.selInstsVar = []
        self.selParamsVar = []
        self.selInsts = []
        self.selParams = []
        self.instBoxes = []
        self.paramBoxes = []
        self.subRows = []
        self.instTraces = []
        self.waitParamBox = None
        self.waitInstTrace = None

        self.title = 'Monitor'
        if not dup:
            self.edit()

    def edit(self, running=False):
        """
        Launch GUI to edit parameters
        
        Parameters
        ----------
        running : boolean
            Parameters will only be editable if we're not running a sequence
        """
        self.running = running
        self.rows = int(self.rows)
        self.labels = [None for x in range(4)]
        self.boxes = [None for x in range(4)]
        self.units = [None for x in range(4)]
        self.waitTrace = None
        self.waitParamTrace = None
        state = tk.DISABLED if self.running else tk.NORMAL
        
        self.updateInstList()

        self.window = tk.Toplevel()
        self.window.resizable(height=False, width=False)
        self.window.grab_set()
        self.window.wm_title('Edit Continuous Measurement')
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW",
                             self.accept)  # if they delete the window, assume they liked their settings

        self.waitVar = tk.StringVar()  # wait for 'Time' or 'Condition'
        self.timeoutVar = tk.DoubleVar()  # how long to wait for each set before proceeding
        self.waitInstVar = tk.StringVar()
        self.waitParamVar = tk.StringVar()  # what (if anything) to wait for
        self.stableTimeVar = tk.DoubleVar()  # How long to require stability
        self.stabilityVar = tk.DoubleVar()  # Stay less than this value away from the final value for the required time
        self.pollTimeVar = tk.DoubleVar()  # Check the value this often
        self.targetVar = tk.DoubleVar()

        self.waitVar.set(self.wait)  # reload values
        self.timeoutVar.set(self.timeout)
        self.waitInstVar.set(self.waitInst)
        self.waitParamVar.set(self.waitParam)
        self.stableTimeVar.set(self.stableTime)
        self.stabilityVar.set(self.stability)
        self.pollTimeVar.set(self.pollTime)
        self.targetVar.set(self.target)

        tk.Label(self.window, text='Poll Time:').grid(column=0, row=0, sticky='NSE', padx=5)
        tk.Label(self.window, text='Timeout:').grid(column=0, row=1, sticky='NSE', padx=5)
        tk.Label(self.window, text='Run until:').grid(column=0, row=2, sticky='NSE', padx=5)

        tk.Entry(self.window, textvariable=self.pollTimeVar, state=state).grid(column=1, row=0, sticky='NSEW')
        tk.Entry(self.window, textvariable=self.timeoutVar, state=state).grid(column=1, row=1, sticky='NSEW')

        tk.Label(self.window, text='s').grid(column=2, row=0, sticky='NSW', padx=5)
        tk.Label(self.window, text='s').grid(column=2, row=1, sticky='NSW', padx=5)

        self.waitBox = ttk.Combobox(self.window, textvariable=self.waitVar, state=state)
        self.waitBox['values'] = ['Time', 'Condition']
        if self.waitVar.get() not in self.waitBox['values']:
            self.waitBox.current(0)
        else:
            self.waitBox.current(self.waitBox['values'].index(self.wait))
        self.waitBox.grid(column=1, row=2, sticky='NSEW', padx=5, columnspan=2)
        self.waitTrace = self.waitVar.trace("w", self.updateWait)

        self.updateWait()

        self.subRows = []
        if not self.running:
            self.addRow = tk.Button(self.window, text='...', command=self.createRow, width=50, state=state)
            self.addRow.grid(column=5, columnspan=4, row=self.rows, sticky='NSEW')

        for ii in range(self.rows):  # how many commands are added here? (default 0 for first edit)
            self.createRow(new=False)
            
        self.updateSize()

        hf.centerWindow(self.window)
        self.gui.root.wait_window(self.window)

    
    def updateSize(self):
        """
        Make sure the edit dialog is large enough to accommodate its content
        """
        print('UPDATESIZE')
        rowpx = self.rowheight*(self.rows+1)
        condpx = self.rowheight*3 if self.waitVar.get() == 'Time' else self.rowheight*7
        height = max((rowpx,condpx))
        print(rowpx,condpx,height)
        width = 550 if self.waitVar.get() == 'Time' else 830
        self.window.geometry('{:d}x{:d}'.format(width,height))
        for ii in range(max(7, self.rows+1)):
            self.window.grid_rowconfigure(ii, weight=0, minsize=self.rowheight)


    def createRow(self, new=True):
        """
        Add a new parameter to measure
        
        Parameters
        ----------
        new : boolean
            If new, initialize with the first inst/param combo.\
            Otherwise, use whatever value was set last time.
        """
        state = tk.DISABLED if self.running else tk.NORMAL
        if new:
            ii = int(self.rows)
            self.rows += 1

        else:
            ii = len(self.instBoxes)  # this is for regenerating the edit window when there's already data

        self.selInstsVar.append(tk.StringVar())  # create variables to store the user's selections
        self.selParamsVar.append(tk.StringVar())

        # generate the box for this row
        self.instBoxes.append(ttk.Combobox(self.window, textvariable=self.selInstsVar[ii], 
                                           width=25, state=state, height=self.rowheight))
        self.instBoxes[ii]['values'] = self.stringInsts[:]
        if new:
            self.instBoxes[ii].current(0)
        else:
            try:
                self.instBoxes[ii].current(self.stringInsts.index(self.selInsts[ii]))
            except ValueError:
                self.instBoxes[ii].current(0)
        self.instBoxes[ii].grid(column=6, row=ii, sticky='NSEW')
        inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]

        if not self.running:
            self.instTraces.append(self.selInstsVar[ii].trace("w", lambda v, n, m, ii=ii: self.updateParams(v, n, m, ii)))

        self.paramBoxes.append(ttk.Combobox(self.window, textvariable=self.selParamsVar[ii],
                                            width=25, state=state, height=self.rowheight))
        stringParams = [str(pm) for pm in inst.getQParams()]
        self.paramBoxes[ii]['values'] = stringParams[:]
        if new:
            self.paramBoxes[ii].current(0)
        else:
            try:
                self.paramBoxes[ii].current(stringParams.index(self.selParams[ii]))
            except ValueError:
                self.paramBoxes[ii].current(0)
        self.paramBoxes[ii].grid(column=7, row=ii, sticky='NSEW')

        # move and rebuild the control buttons
        if not self.running:
            self.subRows.append(tk.Button(self.window, text='X', activeforeground='red',
                                          command=lambda ii=ii: self.destroyRow(ii), height=1))
            self.subRows[ii].grid(column=5, row=ii, sticky='NSEW')
            self.addRow.grid_forget()
            self.addRow.grid(column=5, columnspan=3, row=ii + 1, sticky='NSEW')
        
        self.window.grid_rowconfigure(ii, weight=1, minsize=self.rowheight)
        self.window.grid_rowconfigure(ii+1, weight=1, minsize=self.rowheight)
        self.updateSize()


    def destroyRow(self, ii):
        """
        hitting the little 'X' button to the left removes that row and all its data.
        
        Parameters
        ----------
        ii : int
            row number to delete
        """
        self.rows -= 1

        # clear the actual boxes and labels themselves
        self.instBoxes[ii].destroy()
        del self.instBoxes[ii]
        del self.selInstsVar[ii]
        self.paramBoxes[ii].destroy()
        del self.paramBoxes[ii]
        del self.selParamsVar[ii]

        # move and rebuild the control buttons
        self.subRows[-1].destroy()
        del self.subRows[-1]

        for ii in range(len(self.instBoxes)):
            self.instBoxes[ii].grid_forget()
            self.paramBoxes[ii].grid_forget()
            self.instBoxes[ii].grid(column=6, row=ii, sticky='NSEW')
            self.paramBoxes[ii].grid(column=7, row=ii, sticky='NSEW')

        self.addRow.grid_forget()
        self.addRow.grid(column=5, columnspan=4, row=self.rows, sticky='NSEW')
        self.updateSize()


    def updateUnits(self, *args):
        """
        Make sure the units update when the parameters are updated.
        """
        if self.waitVar.get() == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            unit = param.units
            self.units[0]['text'] = unit
            self.units[1]['text'] = unit

        self.updateValues()


    def updateWait(self, *args):
        """
        Change the structure of the wait half of the GUI
        """
        print('UPDATEWAIT: {:s}'.format(self.waitVar.get()))
        self.updateSize()
        if self.waitVar.get() == 'Time':
            print('a')
            for ii in range(len(self.labels)):
                print('b')
                if self.labels[ii] is not None:
                    self.labels[ii].destroy()
                    self.labels[ii] = None
                if self.boxes[ii] is not None:
                    self.boxes[ii].destroy()
                    self.boxes[ii] = None
                if self.units[ii] is not None:
                    self.units[ii].destroy()
                    self.units[ii] = None
            if self.waitParamTrace is not None:
                print('c')
                self.waitParamVar.trace_vdelete("w", self.waitParamTrace)
                self.waitParamTrace = None
            if self.waitInstTrace is not None:
                print('asdf')
                self.waitInstVar.trace_vdelete("w", self.waitInstTrace)
                self.waitInstTrace = None
            if self.waitParamBox is not None:
                print('d')
                self.waitParamBox.destroy()
                self.waitParamBox = None
            print('y')

        else:  # mode = 'Condition'
            print('e')
            for ii in range(len(self.labels)):
                print('f')
                if self.labels[ii] is not None:
                    print('g')
                    self.labels[ii].destroy()
                    self.labels[ii] = None
                if self.boxes[ii] is not None:
                    print('h')
                    self.boxes[ii].destroy()
                    self.boxes[ii] = None
                if self.units[ii] is not None:
                    print('i')
                    self.units[ii].destroy()
                    self.units[ii] = None
            print('z')

            self.labels[0] = tk.Label(self.window, text='Condition:')  # change first label to proper value
            self.labels[1] = tk.Label(self.window, text='Value:')
            self.labels[2] = tk.Label(self.window, text='Stability Window: +/-')
            self.labels[3] = tk.Label(self.window, text='Stable Time:')

            print('j')
            state = tk.DISABLED if self.running else tk.NORMAL
            self.boxes[0] = ttk.Combobox(self.window, textvariable=self.waitInstVar, width=20, state=state)
            self.boxes[0]['values'] = self.stringInsts[:]
            print('k')
            try:
                self.boxes[0].current(self.stringInsts.index(self.waitInst))
                print('l')
            except ValueError:
                print('m') #*
                print(self.boxes)
                print(self.boxes[0])
                print(self.boxes[0]['values'])
                print(self.stringInsts)
                print(self.boxes[0].current(0))
                self.boxes[0].current(0)
                print('not dead')

            waitInst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            self.waitParamBox = ttk.Combobox(self.window, textvariable=self.waitParamVar, width=20, state=state)
            self.waitParamBox['values'] = [str(pm) for pm in waitInst.getQCSParams()]
            try:
                self.waitParamBox.current([str(pm) for pm in waitInst.getQCSParams()].index(self.waitParam))
                print('n') #*
            except ValueError:
                self.waitParamBox.current(0)
                print('o')

            self.boxes[1] = tk.Entry(self.window, textvariable=self.targetVar, state=state)
            self.boxes[2] = tk.Entry(self.window, textvariable=self.stabilityVar, state=state)
            self.boxes[3] = tk.Entry(self.window, textvariable=self.stableTimeVar, state=state)

            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            unit = param.units
            self.units[0] = tk.Label(self.window, text=unit)
            self.units[1] = tk.Label(self.window, text=unit)
            self.units[2] = tk.Label(self.window, text='s')

            for ii in range(len(self.labels)):
                print('p')
                self.labels[ii].grid(column=0, row=3 + ii, sticky='NSE', padx=5)
                if ii is not 0:
                    print('q')
                    self.boxes[ii].grid(column=1, row=3 + ii, sticky='NSEW', padx=5, columnspan=2)
                    self.boxes[ii].bind('<FocusOut>', self.updateValues)
                    self.units[ii - 1].grid(column=3, row=3 + ii, sticky='NSW', padx=5)

            self.boxes[0].grid(column=1, row=3, sticky='NSEW', padx=5)
            self.waitParamBox.grid(column=2, row=3, sticky='NSEW', padx=5)
            print('r')
            if not self.running:
                self.waitParamTrace = self.waitParamVar.trace("w", self.updateUnits)
                self.waitInstTrace = self.waitInstVar.trace("w", self.updateWaitParams)
                print('s')

        self.updateValues()
        


    def updateValues(self, *args):
        """
        Make sure the values are kosher with the parameter
        """
        if self.waitVar.get() == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            pmax = param.pmax
            pmin = param.pmin

            if pmin is not None:
                self.targetVar.set(max(self.targetVar.get(), pmin))
                self.stabilityVar.set(abs(max(self.stabilityVar.get(), pmin)))

            if pmax is not None:
                self.targetVar.set(min(self.targetVar.get(), pmax))
                self.stabilityVar.set(abs(min(self.stabilityVar.get(), pmax)))

        self.pollTimeVar.set(max(0.1, self.pollTimeVar.get()))


    def accept(self):
        """
        Push all of the parameters to the sequence, then close the window.
        """
        self.updateValues()

        if not self.running:
            if self.waitParamTrace is not None:
                self.waitParamVar.trace_vdelete("w", self.waitParamTrace)
                self.waitParamTrace = None
            self.waitVar.trace_vdelete("w", self.waitTrace)
            if self.waitInstTrace is not None:
                self.waitInstVar.trace_vdelete("w", self.waitInstTrace)
                self.waitInstTrace = None
            for ii in range(self.rows):
                self.selInstsVar[ii].trace_vdelete("w", self.instTraces[ii])
            self.instTraces = []

        self.wait = self.waitVar.get()
        self.timeout = self.timeoutVar.get()
        self.waitInst = self.waitInstVar.get()
        self.waitParam = self.waitParamVar.get()
        self.stableTime = self.stableTimeVar.get()
        self.stability = self.stabilityVar.get()
        self.pollTime = self.pollTimeVar.get()
        self.target = self.targetVar.get()

        self.selInsts = [x.get() for x in self.selInstsVar]
        self.selParams = [x.get() for x in self.selParamsVar]

        self.updateTitle()

        self.window.grab_release()
        self.window.destroy()
        self.addRow = None
        self.stableTimeVar = None
        self.units = []
        self.waitInstVar = None
        self.waitParamVar = None
        self.waitBox = None
        self.addRow = None
        self.pollTimeVar = None
        self.waitVar = None
        self.waitParamBox = None
        self.waitTrace = None
        self.subRow = None
        self.targetVar = None
        self.timeoutVar = None
        self.boxes = []
        self.labels = []
        self.stabilityVar = None
        self.paramBoxes = []
        self.instBoxes = []
        self.selInstsVar = []
        self.selParamsVar = []
        self.subRows = []


    def updateTitle(self):
        """
        Make the title match the contents
        """
        if self.wait == 'Time':
            if self.timeout == 0:
                self.title = 'Monitor indefinitely'
            else:
                self.title = 'Monitor for {:.1f}s'.format(self.timeout)
        else:
            self.title = 'Monitor until {:s} is {:.2f}'.format(self.waitParam, self.target)
        self.title = hf.enumSequence(self.pos, self.title)


    def execute(self, fileReqQ):
        """
        Actually run the sequence
        
        Parameters
        ----------
        fileReqQ : multiprocessing.Queue
            Queue for sending data to the file
        """
        self.stringInsts = [str(x) for x in self.instruments]
        if not self.exp.isAborted():
            waitIter = 0
            starttime = datetime.today()
            timeElapsed = 0
            self.polltime = max(0.1, self.pollTime)  # don't let the user check more often than 10x per second
            datapoints = int(
                self.stableTime / self.polltime)  # number of most recent datapoints to use when checking for stability
            stableData = [self.target + 2 * self.stability for x in
                          range(datapoints)]  # buffer for most recent datapoints: initialize to outside stability window
            timeout = self.timeout  # how long to wait before moving on (regardless of condition
            record = {}

            while timeElapsed <= (timeout if timeout > 0 else 1e7):  # if zero, wait about four months)
                record['Timestamp'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')  # always grab a timestamp

                allInsts = self.selInsts[:]
                allParams = self.selParams[:]
                if self.wait == 'Condition':
                    allInsts.append(self.waitInst)
                    allParams.append(self.waitParam)

                for ii in range(len(allInsts)):
                    inst = self.instruments[self.stringInsts.index(allInsts[ii])]
                    param = inst.getParam(allParams[ii])
                    val = inst.readParam(str(param))
                    if len(val) > 1:
                        for jj, v in enumerate(val):
                            unit = param.units[jj] if param.type == 'cont' else None
                            record[sc.formatHeader(inst, param.comps[jj], unit)] = v
                    else:
                        record[sc.formatHeader(inst, param.name, param.units)] = val[0]

                # Push the data onto the queue for writing the file
                fileReqQ.put(fh.fileRequest('Write Line', record))

                if self.wait == 'Condition':
                    inst = self.instruments[self.stringInsts.index(self.waitInst)]
                    param = inst.getParam(self.waitParam)
                    waitVal = record[sc.formatHeader(inst, param, param.units)]
                    stableData[waitIter % datapoints] = float(waitVal)
                    self.status[1] = 'Condition:  \t{:s} = {:.0f} +/- {:.1f}, {:.0f} s'.format(
                        param.name, self.target, self.stability, self.stableTime)
                    waitIter += 1
                    if abs(max(stableData) - self.target) < self.stability \
                            and abs(min(stableData) - self.target) < self.stability:
                        break

                time.sleep(self.polltime)  # wait for the specified amount of time
                timeElapsed = (datetime.now() - starttime).seconds + (datetime.now() - starttime).microseconds * 1e-6
                self.status[2] = 'Timeout:  \t{:.0f} s/{:.0f} s'.format(np.floor(timeElapsed), self.timeout)
                self.exp.setStatus(self.status)
                if self.exp.isAborted():
                    break


    def getMeasHeaders(self):
        """
        Get a list of all of the data file column headers under which this
        sequence command will generate data.
        
        
        This will be run at the beginning of a sequence to set the file
        structure.
        
        Parameters
        ----------
        self : CMeasCommand
            the command object instance
        
        Returns
        -------
        headers : list of strings
            list of data file column headers
        """
        headers = []
        for ii in range(self.rows):
            inst = self.instruments[self.stringInsts.index(self.selInsts[ii])]
            param = inst.getParam(self.selParams[ii])
            if type(param.comps) is not list:
                if param.type == 'cont':
                    headers.append(sc.formatHeader(inst, param, param.units))
                else:
                    headers.append(sc.formatHeader(inst, param))
            else:
                for ii, comp in enumerate(param.comps):
                    if param.type == 'cont':
                        headers.append(sc.formatHeader(inst, comp, param.units[ii]))
                    else:
                        headers.append(sc.formatHeader(inst, comp))

        if self.wait == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInst)]
            param = inst.getParam(self.waitParam)
            waitHeader = sc.formatHeader(inst, param, param.units)
            if waitHeader not in headers:
                headers.append(waitHeader)

        return headers


    def updateParams(self, v, n, m, ii):
        """
        make sure the parameters match the instruments
        
        Parameters
        ----------
        ii : int
            row number to update
        """
        inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]
        params = inst.getQParams()
        self.paramBoxes[ii]['values'] = params[:]
        self.paramBoxes[ii].current(0)


    def updateWaitParams(self, *args):
        """
        make sure the parameters match the wait instrument
        
        Parameters
        ----------
        ii : int
            row number to update
        """
        inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
        params = [str(pm) for pm in inst.getQCSParams()]
        self.waitParamBox['values'] = params[:]
        self.waitParamBox.current(0)