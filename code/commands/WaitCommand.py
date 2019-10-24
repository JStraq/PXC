import tkinter as tk
from tkinter import ttk
from . import SeqCommand as sc
import FileHandlers as fh
from datetime import datetime
import time
import HelperFunctions as hf

class WaitCmd(sc.SeqCmd):
    cmdname='Wait'
    def __init__(self, exp, app, pos, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.status = ['Status:\tWaiting', 'Condition:\tNone', 'Timeout:\tIndefinite']
        self.type = 'WaitCommand'
        self.timeout = 10.0
        self.conditionInst = ''
        self.conditionParam = ''
        self.conditionVal = 0.0
        self.stableTime = 10.0
        self.stability = 1.0  # Stay less than this value away from the final value for the required time
        self.pollTime = 1.0  # Check the value this often
        self.mode = 'Time'

        self.title = 'Wait'

        if not dup:
           self.edit()

    def edit(self, running=False):
        self.running = running
        self.window = tk.Toplevel(self.gui.root)
        self.window.grab_set()
        self.window.wm_title('Edit Wait Command')
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW",
                            self.accept)  # if they delete the window, assume they liked their settings

        self.instruments = []
        for inst in self.app.instList:
           if inst.name is not None:
               self.instruments.append(inst)
        self.stringInsts = [str(inst) for inst in self.instruments]
        self.timeoutVar = tk.DoubleVar()
        self.conditionInstVar = tk.StringVar()
        self.conditionParamVar = tk.StringVar()
        self.conditionValVar = tk.DoubleVar()
        self.stableTimeVar = tk.DoubleVar()
        self.stabilityVar = tk.DoubleVar()  # Stay less than this value away from the final value for the required time
        self.pollTimeVar = tk.DoubleVar()  # Check the value this often
        self.modeVar = tk.StringVar()

        self.timeoutVar.set(self.timeout)
        self.conditionInstVar.set(self.conditionInst)
        self.conditionParamVar.set(self.conditionParam)
        self.conditionValVar.set(self.conditionVal)
        self.stableTimeVar.set(self.stableTime)
        self.stabilityVar.set(
           self.stability)  # Stay less than this value away from the final value for the required time
        self.pollTimeVar.set(self.pollTime)  # Check the value this often
        self.modeVar.set(self.mode)

        self.labels = [None for x in range(6)]
        self.boxes = [None for x in range(6)]
        self.units = [None for x in range(5)]
        self.paramBox = None
        self.modeTrace = None
        self.unitTrace = None
        self.instTrace = None

        state = tk.DISABLED if self.running else tk.NORMAL
        tk.Label(self.window, text='Wait for:').grid(column=0, row=0, sticky='NSE', padx=5)
        self.modeBox = ttk.Combobox(self.window, textvariable=self.modeVar, width=25, state=state)
        self.modeBox['values'] = ['Time', 'Condition']
        if self.mode not in self.modeBox['values']:
           self.modeBox.current(0)
        else:
           self.modeVar.set(self.mode)
        self.modeBox.grid(column=1, row=0, sticky='NSEW', padx=5)
        self.modeTrace = self.modeVar.trace("w", self.updateMode)

        self.updateMode()
        hf.centerWindow(self.window)
        self.gui.root.wait_window(self.window)

    def updateMode(self, *args):
        state = tk.DISABLED if self.running else tk.NORMAL
        if not self.running:
            if self.unitTrace is not None:
                self.conditionParamVar.trace_vdelete("w", self.unitTrace)
                self.unitTrace = None
            if self.instTrace is not None:
                self.conditionInstVar.trace_vdelete("w", self.instTrace)
                self.instTrace = None

        if self.modeVar.get() == 'Time':  # switched to time, destroy other boxes
            for label in self.labels:  # destroy existing labels
               if label is not None:
                   label.destroy()
               label = None
            for box in self.boxes:  # destroy existing boxes
               if box is not None:
                   box.destroy()
               box = None
            if self.paramBox is not None:
               self.paramBox.destroy()
            for unit in self.units:
               if unit is not None:
                   unit.destroy()
               unit = None
            self.labels[0] = tk.Label(self.window, text='Time (s):')  # put in new label
            self.labels[0].grid(column=0, row=1, sticky='NSEW', padx=5)
            self.boxes[0] = tk.Entry(self.window, textvariable=self.timeoutVar, width=50, state=state)  # put in new box
            self.boxes[0].grid(column=1, row=1, sticky='NSEW', padx=5)

        else:  # mode = 'Condition
            if self.labels[0] is not None:
               self.labels[0].destroy()
            self.labels[0] = tk.Label(self.window, text='Condition:')  # change first label to proper value
            self.labels[1] = tk.Label(self.window, text='Value:')
            self.labels[2] = tk.Label(self.window, text='Stability Window: +/-')
            self.labels[3] = tk.Label(self.window, text='Stable Time:')
            self.labels[4] = tk.Label(self.window, text='Polling Time:')
            self.labels[5] = tk.Label(self.window, text='Timeout (0 waits forever):')
            for ii in range(6):
               self.labels[ii].grid(column=0, row=ii + 1, sticky='NSE', padx=5)

            if self.boxes[0] is not None:
               self.boxes[0].destroy()
            self.boxes[0] = ttk.Combobox(self.window, textvariable=self.conditionInstVar, width=25, state=state)
            self.boxes[0]['values'] =  self.stringInsts
            if self.conditionInstVar.get() not in self.stringInsts:
               self.boxes[0].current(0)
            inst = self.instruments[self.stringInsts.index(self.conditionInstVar.get())]

            self.paramBox = ttk.Combobox(self.window, textvariable=self.conditionParamVar, width=25,state=state)
            self.paramBox['values'] = [str(param) for param in inst.getQCSParams()]

            if self.conditionParamVar.get() not in self.paramBox['values']:
               self.paramBox.current(0)

            self.boxes[1] = tk.Entry(self.window, textvariable=self.conditionValVar, state=state)
            self.boxes[2] = tk.Entry(self.window, textvariable=self.stabilityVar, state=state)
            self.boxes[3] = tk.Entry(self.window, textvariable=self.stableTimeVar, state=state)
            self.boxes[4] = tk.Entry(self.window, textvariable=self.pollTimeVar, state=state)
            self.boxes[5] = tk.Entry(self.window, textvariable=self.timeoutVar, state=state)

            self.boxes[0].grid(column=1, row=1, sticky='NSEW', padx=5)
            self.paramBox.grid(column=2, row=1, sticky='NSEW', padx=5)
            for ii in range(1,6):
               self.boxes[ii].grid(column=1, row=ii + 1, sticky='NSEW', padx=5, columnspan=2)
            if not self.running:
                self.unitTrace = self.conditionParamVar.trace("w", self.updateUnits)
                self.instTrace = self.conditionInstVar.trace("w", self.updateParams)

            self.units[0] = tk.Label(self.window, text='')
            self.units[1] = tk.Label(self.window, text='')
            self.units[2] = tk.Label(self.window, text='s')
            self.units[3] = tk.Label(self.window, text='s')
            self.units[4] = tk.Label(self.window, text='s')

            for ii in range(5):
               self.units[ii].grid(column=3, row=ii + 2, sticky='NSW', padx=5)
            self.updateUnits()

    def updateParams(self, *args):
       inst = self.instruments[self.stringInsts.index(self.conditionInstVar.get())]
       paramStrings = [str(param) for param in inst.getQCSParams()]
       self.paramBox['values'] = paramStrings[:]
       self.paramBox.current(0)

    def updateUnits(self, *args):
       inst = self.instruments[self.stringInsts.index(self.conditionInstVar.get())]
       param = inst.getParam(self.conditionParamVar.get())
       units = param.units
       for ii in range(2):
           self.units[ii]['text'] = units

    def accept(self):
        self.modeVar.trace_vdelete("w", self.modeTrace)
        self.modeTrace = None
        if self.unitTrace is not None:
           self.conditionParamVar.trace_vdelete("w", self.unitTrace)
           self.unitTrace = None
        if self.instTrace is not None:
           self.conditionInstVar.trace_vdelete("w", self.instTrace)
           self.instTrace = None

        self.timeout = self.timeoutVar.get()
        self.conditionInst = self.conditionInstVar.get()
        self.conditionParam = self.conditionParamVar.get()
        self.conditionVal = self.conditionValVar.get()
        self.stableTime = self.stableTimeVar.get()
        self.stability = self.stabilityVar.get()
        self.pollTime = self.pollTimeVar.get()
        self.mode = self.modeVar.get()

        self.window.grab_release()
        self.window.destroy()

        self.updateTitle()

        self.conditionValVar = None
        self.conditionParamVar = None
        self.conditionInstVar = None
        self.modeBox = None
        self.pollTimeVar = None
        self.timeoutVar = None
        self.boxes = []
        self.paramBox = None
        self.labels = []
        self.stableTimeVar = None
        self.stabilityVar = None
        self.modeVar = None
        self.conditionVar = None
        self.units = []

    def updateTitle(self):
        if self.mode == 'Time':
           self.title = 'Wait for {:d}s'.format(int(self.timeout))
        else:
           self.title = 'Wait for {:s} = {:.3f} +/- {:.3f}'.format(str(self.conditionParam), self.conditionVal, self.stability)
        self.title = hf.enumSequence(self.pos, self.title)

    def execute(self, fileReqQ):
        self.stringInsts = [str(x) for x in self.instruments]
        iteration = 0
        starttime = datetime.today()
        timeElapsed = 0
        target = self.conditionVal
        stability = self.stability
        polltime = max(0.1, self.pollTime)  # don't let the user check more often than 10x per second
        datapoints = max(2, int(
           self.stableTime / polltime))  # number of most recent datapoints to use when checking for stability
        stableData = [target + 2 * stability for x in
                     range(datapoints)]  # buffer for most recent datapoints: initialize to outside stability window
        timeout = self.timeout  # how long to wait before moving on (regardless of condition
        if not self.exp.isAborted():
            if self.mode == 'Condition':  # get the actual reference to the instrument so you can read this condition
                inst = self.instruments[self.stringInsts.index(self.conditionInst)]
                param = inst.getParam(self.conditionParam)
                header = sc.formatHeader(str(inst), str(param), param.units)
                self.status[1] = 'Condition:  \t{:s} = {:.0f} +/- {:.1f}, {:.0f} s'.format(
                    header, target, stability, self.stableTime)

            while timeElapsed <= (timeout if timeout > 0 else 1e7):  # if zero, wait forever. ("forever" = 4 months)
                counttime = polltime if self.mode == 'Condition' else 0.2  # how often to check conditions, default is 1s
                time.sleep(counttime)  # wait for the specified amount of time
                timeElapsed = (datetime.now() - starttime).seconds + (datetime.now() - starttime).microseconds * 1e-6

                if self.mode == 'Condition':
                    record = {}
                    measured = inst.readParam(str(param))
                    record[header] = measured[0]
                    record['Timestamp'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')  # always grab a timestamp
                    fileReqQ.put(fh.fileRequest('Write Line', record))  # push to file writing queue
                    stableData[iteration % datapoints] = float(measured[0])
                    iteration += 1
                    if abs(max(stableData) - target) < stability and abs(min(stableData) - target) < stability:
                        break
                else:
                    if timeout is not 0:
                        self.status[2] = 'Timeout:  \t{:.0f} s/{:.0f} s'.format(timeElapsed, self.timeout)
                if self.exp.isAborted():
                    break
                self.exp.setStatus(self.status)

    def getMeasHeaders(self):
        headers = []
        if self.mode == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.conditionInst)]
            param = inst.getParam(self.conditionParam)
            headers = [sc.formatHeader(inst, param, param.units)]
        return headers
