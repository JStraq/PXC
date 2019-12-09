import tkinter as tk
from tkinter import ttk
from . import SeqCommand as sc
import HelperFunctions as hf
from datetime import datetime
import numpy as np
import time
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import FileHandlers as fh


class LoopCmd(sc.SeqCmd):
    """
    command for repeating chunks of code, but varying a parameter each time
    This command has a counterpart ``LoopEnd``, which is a placeholder which
    redirects the sequence back to the top when necessary.
    
    Attributes
    ----------
    mode : str
    spacing : str
    
    """
    cmdname='Loop'
    def __init__(self, exp, app, pos=None, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.type = 'LoopCommand'
        self.status = 'Looping'
        self.iteration = 0
        self.allValues = []

        self.mode = 'Ramp'  # something scans, but how?  modes: 'Ramp' (one way), 'Cycle' (there and back again)
        self.spacing = 'Linear'  # how do you want to space the sampling points?
        self.start = 0.0  # where to start
        self.stop = 1.0  # where to end (used only for ramping)
        self.npoints = 10  # points per direction (entire ramp or each entire cycle)
        self.max = 1  # cycles only
        self.min = -1  # cycles only
        self.dir = 'Up First'  # up first or down first (cycles)
        self.cycles = 1  # number of revolutions around the cycle, supports half-integers

        self.wait = 'Time'  # wait for 'Time' or 'Condition'
        self.timeout = 10.0  # how long to wait for each set before proceeding
        self.sweepInst = ''
        self.sweepParam = ''
        self.waitInst = ''
        self.waitParam = ''  # what (if anything) to wait for
        self.stableTime = 10.0  # How long to require stability
        self.stability = 1.0  # Stay less than this value away from the final value for the required time
        self.pollTime = 1.0  # Check the value this often

        self.title = 'Loop'

        if not dup:
            self.edit()
            
            

    def edit(self, running=False):
        self.updateInstList()
        self.running = running

        self.window = tk.Toplevel(self.gui.root)
        self.window.grab_set()
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW",
                             self.accept)  # if they delete the window, assume they liked their settings
        self.window.wm_title('Edit Loop Command')

        self.labels1 = [None for x in range(7)]
        self.boxes1 = [None for x in range(7)]
        self.units1 = [None for x in range(7)]
        self.labels2 = [None for x in range(5)]
        self.boxes2 = [None for x in range(5)]
        self.units2 = [None for x in range(5)]
        self.instBox = None
        self.paramBox = None
        self.waitParamBox = None
        self.waitInstBox = None
        self.modeTrace = None
        self.waitTrace = None
        self.instTrace1 = None
        self.instTrace2 = None
        self.paramTrace1 = None
        self.paramTrace2 = None

        self.modeVar = tk.StringVar()  # modes: 'Ramp' (one way), 'Cycle' (there and back again)
        self.instVar = tk.StringVar()
        self.paramVar = tk.StringVar()  # which parameter do you want to sweep?
        self.spacingVar = tk.StringVar()  # how do you want to space the sampling points?
        self.startVar = tk.DoubleVar()  # where to start
        self.stopVar = tk.DoubleVar()  # where to end (used only for ramping)
        self.npointsVar = tk.DoubleVar()  # points per direction (entire ramp or each entire cycle)
        self.maxVar = tk.DoubleVar()  # cycles only
        self.minVar = tk.DoubleVar()  # cycles only
        self.dirVar = tk.StringVar()  # up first or down first (cycles)
        self.cyclesVar = tk.DoubleVar()  # number of revolutions around the cycle, supports half-integers

        self.waitVar = tk.StringVar()  # wait for 'Time' or 'Condition'
        self.timeoutVar = tk.DoubleVar()  # how long to wait for each set before proceeding
        self.waitInstVar = tk.StringVar()
        self.waitParamVar = tk.StringVar()  # what (if anything) to wait for
        self.stableTimeVar = tk.DoubleVar()  # How long to require stability
        self.stabilityVar = tk.DoubleVar()  # Stay less than this value away from the final value for the required time
        self.pollTimeVar = tk.DoubleVar()  # Check the value this often

        self.waitVar.set(self.wait)
        self.modeVar.set(self.mode)
        self.instVar.set(self.sweepInst)
        self.paramVar.set(self.sweepParam)
        self.spacingVar.set(self.spacing)
        self.startVar.set(self.start)
        self.stopVar.set(self.stop)
        self.npointsVar.set(self.npoints)
        self.maxVar.set(self.max)
        self.minVar.set(self.min)
        self.dirVar.set(self.dir)
        self.cyclesVar.set(self.cycles)

        self.timeoutVar.set(self.timeout)
        self.waitInstVar.set(self.waitInst)
        self.waitParamVar.set(self.waitParam)
        self.stableTimeVar.set(self.stableTime)
        self.stabilityVar.set(self.stability)
        self.pollTimeVar.set(self.pollTime)  # Check the value this often
        self.modeVar.set(self.mode)

        tk.Label(self.window, text='Parameter to sweep:').grid(column=0, row=0, sticky='NSE', padx=5)

        state = tk.DISABLED if self.running else tk.NORMAL
        self.instBox = ttk.Combobox(self.window, textvariable=self.instVar, width=25, state=state)
        self.instBox['values'] = self.stringInsts
        try:
            self.instBox.current(self.stringInsts.index(self.sweepInst))
        except ValueError:
            self.instBox.current(0)
        self.instBox.grid(column=1, row=0, sticky='NSEW', padx=5, columnspan=2)

        inst = self.instruments[self.stringInsts.index(self.instVar.get())]

        self.paramBox = ttk.Combobox(self.window, textvariable=self.paramVar, width=25, state=state)
        stringParams = [str(pm) for pm in inst.getWCSParams()]
        self.paramBox['values'] = stringParams
        try:
            self.paramBox.current(stringParams.index(self.sweepParam))
        except ValueError:
            self.paramBox.current(0)
        self.paramBox.grid(column=3, row=0, sticky='NSEW', padx=5, columnspan=3)

        tk.Label(self.window, text='Sweep Type:').grid(column=0, row=1, sticky='NSE', padx=5)
        self.modeBox = ttk.Combobox(self.window, textvariable=self.modeVar, state=state)
        self.modeBox.bind('<FocusOut>', self.updateValues)
        self.modeBox['values'] = ['Ramp', 'Cycle']
        if self.modeVar.get() not in self.modeBox['values']:
            self.modeBox.current(0)
        else:
            self.modeBox.current(self.modeBox['values'].index(self.mode))
        self.modeBox.grid(column=1, row=1, sticky='NSEW', padx=5, columnspan=2)


        tk.Label(self.window, text='On step, wait for:').grid(column=3, row=1, sticky='NSE', padx=5)
        self.waitBox = ttk.Combobox(self.window, textvariable=self.waitVar, state=state)
        self.waitBox['values'] = ['Time', 'Condition']
        if self.wait not in self.waitBox['values']:
            self.waitBox.current(0)
        else:
            self.waitBox.current(self.waitBox['values'].index(self.wait))
        self.waitBox.grid(column=4, row=1, sticky='NSEW', padx=5, columnspan=2)
        
        self.figure = Figure(figsize=(3, 3), dpi=75)
        self.subplot = self.figure.add_subplot(111)
        self.plotCanvas = FigureCanvasTkAgg(self.figure, self.window)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=9, column=0, columnspan=6, sticky='NSEW')

        if not self.running:
            self.waitTrace = self.waitVar.trace("w", self.updateWait)
            self.modeTrace = self.modeVar.trace("w", self.updateMode)
            self.instTrace1 = self.instVar.trace("w", self.updateSweepParams)
            self.paramTrace1 = self.paramVar.trace("w", self.updateUnits)

        self.window.resizable(False,False)
        for ii in range(9):
            self.window.grid_rowconfigure(ii, minsize=30)
        self.window.grid_rowconfigure(9, minsize=300)
        
        self.window.grid_columnconfigure(0, minsize=100)
        self.window.grid_columnconfigure(1, minsize=200)
        self.window.grid_columnconfigure(2, minsize=50)
        self.window.grid_columnconfigure(3, minsize=100)
        self.window.grid_columnconfigure(4, minsize=100)
        self.window.grid_columnconfigure(5, minsize=100)


        self.updateMode()
        self.updateWait()
        self.updatePlot(running)

        hf.centerWindow(self.window)
        self.gui.root.wait_window(self.window)


    def updatePlot(self, running=False):   
        self.subplot.clear()
        self.subplot.plot(self.allValues, 'ko-')
        inst = self.instruments[self.stringInsts.index(self.instVar.get())]
        param = inst.getParam(self.paramVar.get())
        try:
            self.subplot.set_ylabel('{:s}-{:s} ({:s})'.format(inst.name, param.name, param.units))
        except:
            self.subplot.set_ylabel('')
        if self.spacingVar.get() == 'Logarithmic':
            self.subplot.set_yscale('log')
        else:
            self.subplot.set_yscale('linear')
        self.canvas.draw()


    def updateUnits(self, *args):
        inst = self.instruments[self.stringInsts.index(self.instVar.get())]
        param = inst.getParam(self.paramVar.get())
        unit = param.units

        if self.modeVar.get() == 'Ramp':
            self.units1[0]['text'] = unit
            self.units1[1]['text'] = unit
        else:
            self.units1[0]['text'] = unit
            self.units1[1]['text'] = unit
            self.units1[2]['text'] = unit

        if self.waitVar.get() == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            unit = param.units
            unit = param.units
            self.units2[1]['text'] = unit

        self.updateValues()


    def updateMode(self, *args):
        state = tk.DISABLED if self.running else tk.NORMAL
        if self.modeVar.get() == 'Ramp':
            for ii in range(len(self.labels1)):
                if self.labels1[ii] is not None:
                    self.labels1[ii].destroy()
                    self.labels1[ii] = None
                if self.boxes1[ii] is not None:
                    self.boxes1[ii].destroy()
                    self.boxes1[ii] = None
                if self.units1[ii] is not None:
                    self.units1[ii].destroy()
                    self.units1[ii] = None

            self.labels1[0] = tk.Label(self.window, text='Start Value:')
            self.labels1[1] = tk.Label(self.window, text='End Value:')
            self.labels1[2] = tk.Label(self.window, text='Number of Points:')
            self.labels1[3] = tk.Label(self.window, text='Spacing:')

            self.boxes1[0] = tk.Entry(self.window, textvariable=self.startVar, state=state)
            self.boxes1[1] = tk.Entry(self.window, textvariable=self.stopVar, state=state)
            self.boxes1[2] = tk.Entry(self.window, textvariable=self.npointsVar, state=state)
            self.boxes1[3] = ttk.Combobox(self.window, textvariable=self.spacingVar, state=state)
            
            self.boxes1[3]['values'] = ['Linear',
                                        'Logarithmic',
                                        'Sinusoidal',
                                        'Uniform Random']
            
            if self.spacingVar.get() not in self.boxes1[3]['values']:
                self.boxes1[3].current(0)

            inst = self.instruments[self.stringInsts.index(self.instVar.get())]
            param = inst.getParam(self.paramVar.get())
            unit = param.units
            unit = param.units
            self.units1[0] = tk.Label(self.window, text=unit)
            self.units1[1] = tk.Label(self.window, text=unit)

            for ii in range(len(self.labels1)):
                if self.labels1[ii] is not None:
                    self.labels1[ii].grid(column=0, row=2 + ii, sticky='NSE', padx=5)
                if self.boxes1[ii] is not None:
                    self.boxes1[ii].grid(column=1, row=2 + ii, sticky='NSEW', padx=5)
                    if not self.running:
                        self.boxes1[ii].bind('<FocusOut>', self.updateValues)
                if self.units1[ii] is not None:
                    self.units1[ii].grid(column=2, row=2 + ii, sticky='NSW', padx=5)

        else:  # mode = 'Cycle'
            for ii in range(len(self.labels1)):
                if self.labels1[ii] is not None:
                    self.labels1[ii].destroy()
                    self.labels1[ii] = None
                if self.boxes1[ii] is not None:
                    self.boxes1[ii].destroy()
                    self.boxes1[ii] = None
                if self.units1[ii] is not None:
                    self.units1[ii].destroy()
                    self.units1[ii] = None

            self.labels1[0] = tk.Label(self.window, text='Start Value:')
            self.labels1[1] = tk.Label(self.window, text='Max Value:')
            self.labels1[2] = tk.Label(self.window, text='Min Value:')
            self.labels1[3] = tk.Label(self.window, text='Number of Points:')
            self.labels1[4] = tk.Label(self.window, text='Spacing:')
            self.labels1[5] = tk.Label(self.window, text='Number of Cycles:')
            self.labels1[6] = tk.Label(self.window, text='Direction:')

            self.boxes1[0] = tk.Entry(self.window, textvariable=self.startVar, state=state)
            self.boxes1[1] = tk.Entry(self.window, textvariable=self.maxVar, state=state)
            self.boxes1[2] = tk.Entry(self.window, textvariable=self.minVar, state=state)
            self.boxes1[3] = tk.Entry(self.window, textvariable=self.npointsVar, state=state)
            self.boxes1[4] = ttk.Combobox(self.window, textvariable=self.spacingVar, state=state)
            self.boxes1[4]['values'] = ['Linear',
                                        'Logarithmic',
                                        'Sinusoidal',
                                        'Uniform Random']
            if self.spacingVar.get() not in self.boxes1[4]['values']:
                self.boxes1[4].current(0)
            self.boxes1[5] = tk.Entry(self.window, textvariable=self.cyclesVar, state=state)
            self.boxes1[6] = ttk.Combobox(self.window, textvariable=self.dirVar, state=state)
            self.boxes1[6]['values'] = ['Up First', 'Down First']
            if self.dirVar.get() not in self.boxes1[6]['values']:
                self.boxes1[6].current(0)

            inst = self.instruments[self.stringInsts.index(self.instVar.get())]
            param = inst.getParam(self.paramVar.get())
            unit = param.units
            unit = param.units
            self.units1[0] = tk.Label(self.window, text=unit)
            self.units1[1] = tk.Label(self.window, text=unit)
            self.units1[2] = tk.Label(self.window, text=unit)

            for ii in range(len(self.labels1)):
                if self.labels1[ii] is not None:
                    self.labels1[ii].grid(column=0, row=2 + ii, sticky='NSE', padx=5)
                if self.boxes1[ii] is not None:
                    self.boxes1[ii].grid(column=1, row=2 + ii, sticky='NSEW', padx=5)
#                    if type(self.boxes1[ii]) == tk.Entry:
                    self.boxes1[ii].bind('<FocusOut>', self.updateValues)
                if self.units1[ii] is not None:
                    self.units1[ii].grid(column=2, row=2 + ii, sticky='NSW', padx=5)



    def updateWait(self, *args):
        state = tk.DISABLED if self.running else tk.NORMAL
        if self.waitVar.get() == 'Time':
            for ii in range(len(self.labels2)):
                if self.labels2[ii] is not None:
                    self.labels2[ii].destroy()
                    self.labels2[ii] = None
                if self.boxes2[ii] is not None:
                    self.boxes2[ii].destroy()
                    self.boxes2[ii] = None
                if self.units2[ii] is not None:
                    self.units2[ii].destroy()
                    self.units2[ii] = None
            if self.paramTrace2 is not None:
                self.waitParamVar.trace_vdelete("w", self.paramTrace2)
                self.paramTrace2 = None
            if self.instTrace2 is not None:
                self.waitInstVar.trace_vdelete("w", self.instTrace2)
                self.instTrace2 = None
            if self.waitParamBox is not None:
                self.waitParamBox.destroy()
                self.waitParamBox = None

            self.labels2[0] = tk.Label(self.window, text='Delay Time:')

            self.boxes2[0] = tk.Entry(self.window, textvariable=self.timeoutVar, state=state)

            self.units2[0] = tk.Label(self.window, text='s')

            self.labels2[0].grid(column=3, row=2, sticky='NSE', padx=5)
            self.boxes2[0].grid(column=4, row=2, sticky='NSEW', padx=5)
            self.units2[0].grid(column=5, row=2, sticky='NSW', padx=5)

        else:  # mode = 'Condition
            for ii in range(len(self.labels2)):
                if self.labels2[ii] is not None:
                    self.labels2[ii].destroy()
                    self.labels2[ii] = None
                if self.boxes2[ii] is not None:
                    self.boxes2[ii].destroy()
                    self.boxes2[ii] = None
                if self.units2[ii] is not None:
                    self.units2[ii].destroy()
                    self.units2[ii] = None

            self.labels2[0] = tk.Label(self.window, text='Condition:')  # change first label to proper value
            self.labels2[1] = tk.Label(self.window, text='Stability Window: +/-')
            self.labels2[2] = tk.Label(self.window, text='Stable Time:')
            self.labels2[3] = tk.Label(self.window, text='Polling Time:')
            self.labels2[4] = tk.Label(self.window, text='Timeout (0 waits forever):')

            self.boxes2[0] = ttk.Combobox(self.window, textvariable=self.waitInstVar, width=20, state=state)
            self.boxes2[0]['values'] = self.stringInsts[:]
            if self.waitInstVar.get() not in self.boxes2[0]['values']:
                self.boxes2[0].current(0)
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]

            self.waitParamBox = ttk.Combobox(self.window, textvariable=self.waitParamVar, width=20, state=state)
            stringParams = [str(pm) for pm in inst.getQCSParams()]
            self.waitParamBox['values'] = stringParams
            if self.waitParamVar.get() not in self.boxes2[0]['values']:
                self.waitParamBox.current(0)
            param = inst.getParam(self.waitParamVar.get())

            self.boxes2[1] = tk.Entry(self.window, textvariable=self.stabilityVar, state=state)
            self.boxes2[2] = tk.Entry(self.window, textvariable=self.stableTimeVar, state=state)
            self.boxes2[3] = tk.Entry(self.window, textvariable=self.pollTimeVar, state=state)
            self.boxes2[4] = tk.Entry(self.window, textvariable=self.timeoutVar, state=state)

            unit = param.units
            self.units2[1] = tk.Label(self.window, text=unit)
            self.units2[2] = tk.Label(self.window, text='s')
            self.units2[3] = tk.Label(self.window, text='s')
            self.units2[4] = tk.Label(self.window, text='s')

            for ii in range(len(self.labels2)):
                if self.labels2[ii] is not None:
                    self.labels2[ii].grid(column=3, row=2 + ii, sticky='NSE', padx=5)
                if self.boxes2[ii] is not None and ii is not 0:
                    self.boxes2[ii].grid(column=4, row=2 + ii, sticky='NSEW', padx=5)
#                    if type(self.boxes2[ii]) == tk.Entry:
                    self.boxes2[ii].bind('<FocusOut>', self.updateValues)
                if self.units2[ii] is not None:
                    self.units2[ii].grid(column=5, row=2 + ii, sticky='NSW', padx=5)
            self.boxes2[0].grid(column=4, row=2, sticky='NSEW', padx=5)
            self.waitParamBox.grid(column=5, row=2, sticky='NSEW', padx=5)

            if not self.running:
                self.instTrace2 = self.waitInstVar.trace("w", self.updateWaitParams)
                self.paramTrace2 = self.waitParamVar.trace("w", self.updateUnits)

        self.updateValues()



    def updateValues(self, *args):
        inst = self.instruments[self.stringInsts.index(self.instVar.get())]
        param = inst.getParam(self.paramVar.get())
        pmax = param.pmax
        pmin = param.pmin

        # round number of points to int, number of cycles to half-integer
        n = self.npointsVar.get()
        try:
            n = float(n)
        except ValueError:
            n = 0
        self.npointsVar.set(max(2, round(n)))
        self.cyclesVar.set(round(self.cyclesVar.get() * 2) / 2)
        
        # prevent log of negative numbers
        if self.spacingVar.get() == 'Logarithmic':
            if self.startVar.get() <= 0:
                self.startVar.set(max(self.startVar.get(), 1e-9))
            if self.stopVar.get() <= 0:            
                self.stopVar.set(max(self.stopVar.get(), 1e-9))
            if self.maxVar.get() <= 0:
                self.maxVar.set(max(self.maxVar.get(), 1e-9))
            if self.minVar.get() <= 0:
                self.minVar.set(max(self.minVar.get(), 1e-9))

        # first coerce to within parameter limits
        if pmin is not None:
            self.startVar.set(max(self.startVar.get(), pmin))
            self.stopVar.set(max(self.stopVar.get(), pmin))
            self.maxVar.set(max(self.maxVar.get(), pmin))
            self.minVar.set(max(self.minVar.get(), pmin))

        if pmax is not None:
            self.startVar.set(min(self.startVar.get(), pmax))
            self.stopVar.set(min(self.stopVar.get(), pmax))
            self.maxVar.set(min(self.maxVar.get(), pmax))
            self.minVar.set(min(self.minVar.get(), pmax))

        # then force the cycle data to make intuitive sense (max >= start >= min)
        if self.modeVar.get() == 'Cycle':
            self.minVar.set(min(self.minVar.get(), self.startVar.get()))
            self.maxVar.set(max(self.maxVar.get(), self.startVar.get()))

        if self.waitVar.get() == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
            param = inst.getParam(self.waitParamVar.get())
            self.pollTimeVar.set(max(0.1, self.pollTimeVar.get()))

        # actually build the arrays of values
        if self.modeVar.get() == 'Ramp':
            if self.spacingVar.get() == 'Linear':
                self.allValues = np.linspace(self.startVar.get(), self.stopVar.get(), self.npointsVar.get())
                
            elif self.spacingVar.get() == 'Logarithmic':
                self.allValues = np.logspace(np.log10(self.startVar.get()), np.log10(self.stopVar.get()),
                                             self.npointsVar.get())
                                             
            elif self.spacingVar.get() == 'Sinusoidal':
                x = np.linspace(0, np.pi/2, self.npointsVar.get())
                self.allValues = self.startVar.get() + (self.stopVar.get() - self.startVar.get())*np.sin(x)
                
            elif self.spacingVar.get() == 'Uniform Random':
                self.allValues = np.linspace(self.startVar.get(), self.stopVar.get(), self.npointsVar.get())
                random.shuffle(self.allValues)

        else:  # Cycle
            if self.spacingVar.get() == 'Linear':
                try:
                    nup = abs(self.npointsVar.get() * (self.maxVar.get() - self.startVar.get()) / (
                        self.maxVar.get() - self.minVar.get()))
                except ZeroDivisionError:
                    nup = 0
                try:
                    ndown = abs(self.npointsVar.get() * (self.startVar.get() - self.minVar.get()) / (
                        self.maxVar.get() - self.minVar.get()))
                except ZeroDivisionError:
                    ndown = 0
                upcycle = np.linspace(self.startVar.get(), self.maxVar.get(), np.ceil(nup / 2))
                downcycle = np.linspace(self.startVar.get(), self.minVar.get(), np.ceil(ndown / 2))
                
                upcycle = np.concatenate((upcycle, upcycle[::-1][1:]))
                downcycle = np.concatenate((downcycle, downcycle[::-1][1:]))
    
                self.allValues = np.array([self.startVar.get()])
                dirflag = 1 if self.dirVar.get() == 'Up First' else 0
                for ii in range(int(self.cyclesVar.get() * 2)):
                    thiscycle = downcycle if (ii % 2 == dirflag) else upcycle
                    self.allValues = np.append(self.allValues, thiscycle[1:])

            elif self.spacingVar.get() == 'Logarithmic':
                try:
                    nup = self.npointsVar.get() * (np.log10(self.maxVar.get()) - np.log10(self.startVar.get())) / (
                        np.log10(self.maxVar.get()) - np.log10(self.minVar.get()))
                except ZeroDivisionError:
                    nup = 0
                try:
                    ndown = self.npointsVar.get() * (np.log10(self.startVar.get()) - np.log10(self.minVar.get())) / (
                        np.log10(self.maxVar.get()) - np.log10(self.minVar.get()))
                except ZeroDivisionError:
                    ndown = 0

                upcycle = np.logspace(np.log10(self.startVar.get()), np.log10(self.maxVar.get()), np.ceil(nup / 2))
                downcycle = np.logspace(np.log10(self.startVar.get()), np.log10(self.minVar.get()), np.ceil(ndown / 2))
                
                upcycle = np.concatenate((upcycle, upcycle[::-1][1:]))
                downcycle = np.concatenate((downcycle, downcycle[::-1][1:]))
    
                self.allValues = np.array([self.startVar.get()])
                dirflag = 1 if self.dirVar.get() == 'Up First' else 0
                for ii in range(int(self.cyclesVar.get() * 2)):
                    thiscycle = downcycle if (ii % 2 == dirflag) else upcycle
                    self.allValues = np.append(self.allValues, thiscycle[1:])
            
            elif self.spacingVar.get() == 'Sinusoidal':
                n = np.arange(self.npointsVar.get())
                m = self.cyclesVar.get()
                if float(int(m))==float(m):
                    n = np.hstack((np.tile(n, int(m)), n[0]))
                else:
                    n = np.hstack((np.tile(n[:-1], np.floor(m)), n[-1], n[:int(len(m)/2)]))
                if self.dirVar.get() == 'Down First':
                    n = n[::-1]
                offs = (self.maxVar.get() + self.minVar.get())/2
                amp = (self.maxVar.get() - self.minVar.get())/2
                try:
                    phase = np.arcsin((self.startVar.get()-offs)/amp)
                except ZeroDivisionError:
                    phase = 0
                self.allValues = amp*np.sin(2*np.pi*n/self.npointsVar.get() + phase)+ offs
                
            elif self.spacingVar.get() == 'Uniform Random':
                vals = np.linspace(self.minVar.get(), self.maxVar.get(), self.npointsVar.get())
                m = self.cyclesVar.get()
                if float(int(m))==float(m):
                    vals = (np.tile(vals[:-1], int(m)))
                else:
                    vals = np.hstack((np.tile(vals[:-1], np.floor(m)), n[-1], n[:int(len(vals)/2)]))
                self.allValues = vals
                random.shuffle(self.allValues)
                
            

        self.updatePlot()


    def updateSweepParams(self, *args):
        inst = self.instruments[self.stringInsts.index(self.instVar.get())]
        params = inst.getWCSParams()
        self.paramBox['values'] = params[:]
        self.paramBox.current(0)
        self.updateValues()



    def updateWaitParams(self, *args):
        inst = self.instruments[self.stringInsts.index(self.waitInstVar.get())]
        params = inst.getQCSParams()
        self.waitParamBox['values'] = params[:]
        try:
            self.waitParamBox.current(params.index(self.waitParam))
        except ValueError:
            self.waitParamBox.current(0)
        self.updateValues()


    def accept(self):
        self.updateValues()
        if not self.running:
            self.paramVar.trace_vdelete("w", self.paramTrace1)
            if self.paramTrace2 is not None:
                self.waitParamVar.trace_vdelete("w", self.paramTrace2)
                self.paramTrace2 = None
            self.modeVar.trace_vdelete("w", self.modeTrace)
            self.waitVar.trace_vdelete("w", self.waitTrace)

        self.mode = self.modeVar.get()
        self.sweepParam = self.paramVar.get()
        self.sweepInst = self.instVar.get()
        self.spacing = self.spacingVar.get()
        self.start = self.startVar.get()
        self.stop = self.stopVar.get()
        self.npoints = self.npointsVar.get()
        self.max = self.maxVar.get()
        self.min = self.minVar.get()
        self.dir = self.dirVar.get()
        self.cycles = self.cyclesVar.get()

        self.wait = self.waitVar.get()
        self.timeout = self.timeoutVar.get()
        self.waitInst = self.waitInstVar.get()
        self.waitParam = self.waitParamVar.get()
        self.stableTime = self.stableTimeVar.get()
        self.stability = self.stabilityVar.get()
        self.pollTime = self.pollTimeVar.get()
        self.mode = self.modeVar.get()

        self.updateTitle()

        self.window.grab_release()
        self.window.destroy()

        self.units1 = []
        self.units2 = []
        self.waitInstVar = None
        self.waitParamVar = None
        self.cyclesVar = None
        self.modeVar = None
        self.npointsVar = None
        self.pollTimeVar = None
        self.waitVar = None
        self.stabilityVar = None
        self.boxes1 = []
        self.boxes2 = []
        self.labels1 = []
        self.labels2 = []
        self.paramBox = None
        self.instBox = None
        self.stableTimeVar = None
        self.paramVar = None
        self.instVar = None
        self.spacingVar = None
        self.timeoutVar = None
        self.waitBox = None
        self.minVar = None
        self.maxVar = None
        self.modeBox = None
        self.waitParamBox = None
        self.waitTrace = None
        self.paramTrace1 = None
        self.paramTrace2 = None
        self.instTrace1 = None
        self.instTrace2 = None
        self.dirVar = None
        self.startVar = None
        self.modeTrace = None
        self.stopVar = None


    def isDone(self):
        return self.iteration >= len(self.allValues)


    def execute(self, fileReqQ):
        if not self.exp.isAborted():
            inst = self.instruments[self.stringInsts.index(self.sweepInst)]
            param = inst.getParam(self.sweepParam)
            inst.writeParam(str(param), self.allValues[self.iteration])
            thisVal = self.allValues[self.iteration]
            self.iteration += 1
            self.updateTitle()
            self.status = '{:s}, {:d}/{:d}'.format(hf.shortenLoop(self.title), int(self.iteration), int(self.npoints))
            self.exp.setStatusLoop(self.status)

            waitIter = 0
            starttime = datetime.today()
            timeElapsed = 0
            target = float(thisVal)
            stability = float(self.stability)
            polltime = max(0.1, self.pollTime)  # don't let the user check more often than 10x per second
            datapoints = int(self.stableTime / polltime)  # number of most recent datapoints to use for stability check
            stableData = [target + 2 * stability for x in
                          range(datapoints)]  # buffer for most recent datapoints: initialize to outside stability window
            timeout = self.timeout  # how long to wait before moving on (regardless of condition

            if self.wait == 'Condition':  # get the actual reference to the instrument so you can read this condition
                wInst = self.instruments[self.stringInsts.index(self.waitInst)]
                wParam = inst.getParam(self.waitParam)

            while timeElapsed <= (timeout if (timeout > 0) else 1e7):
                if self.wait == 'Time' and self.timeout==0:
                    break
                else:
                    time.sleep(polltime)  # wait for the specified amount of time
                    timeElapsed = (datetime.now() - starttime).seconds + (datetime.now() - starttime).microseconds * 1e-6

                if self.wait == 'Condition':
                    record = {}
                    measured = wInst.readParam(str(wParam))
                    record[sc.formatHeader(wInst,wParam, wParam.units)] = measured[0]
                    record['Timestsc.amp'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f') # always grab a timestamp
                    fileReqQ.put(fh.fileRequest('Write Line', record))  # push to file writing queue
                    stableData[waitIter % datapoints] = float(measured[0])
                    waitIter += 1
                    if abs(max(stableData) - target) < stability and abs(min(stableData) - target) < stability:
                        break
                if self.exp.isAborted():
                    break



    def updateTitle(self):
        loopNum = 1
        try:
            self.pos = self.app.sequence.index(self)
        except ValueError: pass
        for cmd in self.app.sequence[:self.pos]:
            if type(cmd) is LoopCmd:
                loopNum += 1
        self.title = 'Loop {:d}: {:s} {:s}'.format(loopNum, self.mode, self.sweepParam)

        self.title = hf.enumSequence(self.pos, self.title)

        for jj, cmd in enumerate(self.app.sequence):
            if type(cmd) == LoopEnd:
                if cmd.loop == self:
                    cmd.title = 'End Loop {:d}'.format(loopNum)
                    cmd.title = hf.enumSequence(self.pos, self.title)



    def getMeasHeaders(self):
        headers = []
        if self.wait == 'Condition':
            inst = self.instruments[self.stringInsts.index(self.waitInst)]
            param = inst.getParam(self.waitParam)
            headers.append(sc.formatHeader(inst,param, param.units))
        return headers





class LoopEnd(sc.SeqCmd):
    def __init__(self, exp, app, pos=None, dup=False, gui=None, loop=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.loop = loop

        self.title = 'Loop End'
        self.type = 'LoopEndCommand'
        if not dup:
            self.loopPos = self.app.sequence.index(self.loop)



    def execute(self, fileReqQ):
        if not self.loop.isDone() and not self.exp.isAborted():
            return self.app.sequence.index(self.loop)
        else:
            self.exp.setStatusLoop('')
            self.loop.iteration = 0  # reset the counter for the next run!
            return None



    def edit(self, running=False):
        self.loop.edit(running=running)



    def updateTitle(self):
        loopNum = 1
        for cmd in self.app.sequence[:self.loop.pos]:
            if type(cmd) is LoopCmd:
                loopNum += 1
        self.loopPos = self.app.sequence.index(self.loop)
        self.title = 'End Loop {:d}'.format(loopNum)
        self.title = hf.enumSequence(self.pos, self.title)



    def getMeasHeaders(self):
        return []