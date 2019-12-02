import tkinter as tk
from tkinter import ttk
from . import SeqCommand as sc
import FileHandlers as fh
from datetime import datetime
import time
import HelperFunctions as hf
import numpy as np


class CMeasCmd(sc.SeqCmd):  # Repeatedly measures a list of parameters
    cmdname = 'Continuous Measurement'
    def __init__(self, exp, app, pos, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.status = self.status = ['Status: \tMeasuring', 'Condition:\t', 'Parameter:\t']
        self.type = 'ContinuousMeasurementCommand'
        self.rows = 0

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
        self.running = running
        self.rows = int(self.rows)
        self.labels = [None for x in range(4)]
        self.boxes = [None for x in range(4)]
        self.units = [None for x in range(4)]
        self.waitTrace = None
        self.paramTrace = None
        state = tk.DISABLED if self.running else tk.NORMAL
        
        self.updateInstList()

        self.window = tk.Toplevel()
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

        hf.centerWindow(self.window)
        self.gui.root.wait_window(self.window)

    def createRow(self, new=True):
        state = tk.DISABLED if self.running else tk.NORMAL
        if new:
            ii = int(self.rows)
            self.rows += 1

        else:
            ii = len(self.instBoxes)  # this is for regenerating the edit window when there's already data

        self.selInstsVar.append(tk.StringVar())  # create variables to store the user's selections
        self.selParamsVar.append(tk.StringVar())

        # generate the box for this row
        self.instBoxes.append(ttk.Combobox(self.window, textvariable=self.selInstsVar[ii], width=25, state=state))
        self.instBoxes[ii]['values'] = self.stringInsts[:]
        if new:
            self.instBoxes[ii].current(0)
        else:
            try:
                self.instBoxes[ii].current(self.stringInsts.index(self.selInsts[ii]))
            except ValueError:
                self.instBoxes[ii].current(0)
        self.instBoxes[ii].grid(column=6, row=ii)
        inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]

        if not self.running:
            self.instTraces.append(self.selInstsVar[ii].trace("w", lambda v, n, m, ii=ii: self.updateParams(v, n, m, ii)))

        self.paramBoxes.append(ttk.Combobox(self.window, textvariable=self.selParamsVar[ii], width=25, state=state))
        stringParams = [str(pm) for pm in inst.getQParams()]
        self.paramBoxes[ii]['values'] = stringParams[:]
        if new:
            self.paramBoxes[ii].current(0)
        else:
            try:
                self.paramBoxes[ii].current(stringParams.index(self.selParams[ii]))
            except ValueError:
                self.paramBoxes[ii].current(0)
        self.paramBoxes[ii].grid(column=7, row=ii)

        # move and rebuild the control buttons
        if not self.running:
            self.subRows.append(tk.Button(self.window, text='X', activeforeground='red', command=lambda ii=ii: self.destroyRow(ii)))
            self.subRows[ii].grid(column=5, row=ii)
            self.addRow.grid_forget()
            self.addRow.grid(column=5, columnspan=3, row=ii + 1, sticky='NSEW')

    def destroyRow(self, ii):  # hitting the little 'X' button to the left removes that row and all its data.
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

    def updateUnits(self, *args):
        if self.waitVar.get() == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            unit = param.units
            self.units[0]['text'] = unit
            self.units[1]['text'] = unit

        self.updateValues()

    def updateWait(self, *args):
        if self.waitVar.get() == 'Time':
            for ii in range(len(self.labels)):
                if self.labels[ii] is not None:
                    self.labels[ii].destroy()
                    self.labels[ii] = None
                if self.boxes[ii] is not None:
                    self.boxes[ii].destroy()
                    self.boxes[ii] = None
                if self.units[ii] is not None:
                    self.units[ii].destroy()
                    self.units[ii] = None
            if self.paramTrace is not None:
                self.waitParamVar.trace_vdelete("w", self.paramTrace)
                self.paramTrace = None
            if self.waitParamBox is not None:
                self.waitParamBox.destroy()
                self.waitParamBox = None

        else:  # mode = 'Condition
            for ii in range(len(self.labels)):
                if self.labels[ii] is not None:
                    self.labels[ii].destroy()
                    self.labels[ii] = None
                if self.boxes[ii] is not None:
                    self.boxes[ii].destroy()
                    self.boxes[ii] = None
                if self.units[ii] is not None:
                    self.units[ii].destroy()
                    self.units[ii] = None

            self.labels[0] = tk.Label(self.window, text='Condition:')  # change first label to proper value
            self.labels[1] = tk.Label(self.window, text='Value:')
            self.labels[2] = tk.Label(self.window, text='Stability Window: +/-')
            self.labels[3] = tk.Label(self.window, text='Stable Time:')

            state = tk.DISABLED if self.running else tk.NORMAL
            self.boxes[0] = ttk.Combobox(self.window, textvariable=self.waitInstVar, width=20, state=state)
            self.boxes[0]['values'] = self.stringInsts[:]
            try:
                self.boxes[0].current(self.stringInsts.index(self.waitInst))
            except ValueError:
                self.boxes[0].current(0)

            waitInst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            self.waitParamBox = ttk.Combobox(self.window, textvariable=self.waitParamVar, width=20, state=state)
            self.waitParamBox['values'] = [str(pm) for pm in waitInst.getQCSParams()]
            try:
                self.waitParamBox.current([str(pm) for pm in waitInst.getQCSParams()].index(self.waitParam))
            except ValueError:
                self.waitParamBox.current(0)

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
                self.labels[ii].grid(column=0, row=3 + ii, sticky='NSE', padx=5)
                if ii is not 0:
                    self.boxes[ii].grid(column=1, row=3 + ii, sticky='NSEW', padx=5, columnspan=2)
                    self.boxes[ii].bind('<FocusOut>', self.updateValues)
                    self.units[ii - 1].grid(column=3, row=3 + ii, sticky='NSW', padx=5)

            self.boxes[0].grid(column=1, row=3, sticky='NSEW', padx=5)
            self.waitParamBox.grid(column=2, row=3, sticky='NSEW', padx=5)
            if not self.running:
                self.paramTrace = self.waitParamVar.trace("w", self.updateUnits)
                self.waitInstTrace = self.waitInstVar.trace("w", self.updateWaitParams)

        self.updateValues()

    def updateValues(self, *args):
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
        self.updateValues()

        if not self.running:
            if self.paramTrace is not None:
                self.waitParamVar.trace_vdelete("w", self.paramTrace)
                self.paramTrace = None
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
        if self.wait == 'Time':
            if self.timeout == 0:
                self.title = 'Monitor indefinitely'
            else:
                self.title = 'Monitor for {:.1f}s'.format(self.timeout)
        else:
            self.title = 'Monitor until {:s} is {:.2f}'.format(self.waitParam, self.target)
        self.title = hf.enumSequence(self.pos, self.title)

    def execute(self, fileReqQ):
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
                        param, self.target, self.stability, self.stableTime)
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
        inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]
        params = inst.getQParams()
        self.paramBoxes[ii]['values'] = params[:]
        self.paramBoxes[ii].current(0)

    def updateWaitParams(self, *args):
        inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
        params = [str(pm) for pm in inst.getQCSParams()]
        self.waitParamBox['values'] = params[:]
        self.waitParamBox.current(0)