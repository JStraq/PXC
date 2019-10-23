import tkinter as tk
from tkinter import ttk
from lib.commands import SeqCommand as sc
from lib import FileHandlers as fh
from datetime import datetime
from lib import HelperFunctions as hf

class SMeasCmd(sc.SeqCmd):  # PERFORM A SINGLE POINT MEASUREMENT OF THE SELECTED ITEMS
    cmdname = 'Single Measurement'
    def __init__(self, exp, app, pos, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.rows = 0
        self.title = 'Single Measurement'
        self.status = ['Status: \tMeasuring', 'Instrument:\t', 'Parameter:\t']
        self.type = 'SingleMeasurementCommand'
        self.selParams = []
        self.selInsts = []
        self.subRows = []
        if not dup:
            self.edit()

    def execute(self, fileReqQ):
        # query the selected values to the selected parameters on the selected instruments, write to file
        if not self.exp.isAborted():
            record = dict()
            record['Timestamp'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f')  # always grab a timestamp

            for ii in range(len(self.selInsts)):
                inst = self.instruments[self.stringInsts.index(self.selInsts[ii])]
                param = inst.getParam(self.selParams[ii])
                self.status[1] = 'Instrument:\t{:s}'.format(str(inst))
                self.status[2] = 'Parameter:\t{:s}'.format(str(param))
                val = inst.readParam(str(param))  # returns a list, even if there's only one element
                try:
                    if len(val) > 1:
                        for jj, v in enumerate(val):
                            try:
                                unit = param.units[jj]
                            except IndexError:
                                unit = None
                            try:
                                record[sc.formatHeader(inst, param.comps[jj], unit)] = v
                            except (IndexError, TypeError):
                                record[sc.formatHeader(inst, param.name, unit)] = val
                    else:
                        record[sc.formatHeader(inst, param.name, param.units)] = val[0]
                except TypeError:
                   print('Instrument error: could not get a value for parameter {:s} on {:s}'.format(str(param), str(inst)))
            print(record)
            fileReqQ.put(fh.fileRequest('Write Line', record))  # push to file writing queue

    def accept(self):  # if the window is closed, destroy widgets on the window
       self.selInsts = [x.get() for x in self.selInstsVar]
       self.selParams = [x.get() for x in self.selParamsVar]

       self.updateTitle()

       self.window.grab_release()
       self.window.destroy()

       self.instBoxes = []
       self.paramBoxes = []
       self.subRows = []
       self.selInstsVar = []
       self.selParamsVar = []
       self.addRow = []
       self.instTraces = []

    def updateTitle(self):
       if len(self.selParams) == 0:
           self.title = 'Measure (Nothing)'
       elif len(self.selParams) == 1:
           self.title = 'Measure ' + self.selParams[0]
       elif len(self.selParams) == 2:
           self.title = 'Measure ' + self.selParams[0] + ', ' + self.selParams[1]
       else:
           self.title = 'Measure ' + self.selParams[0] + ', ' + self.selParams[1] + ', ...'
       self.title = hf.enumSequence(self.pos, self.title)

    def edit(self, running=False):  # OPEN A WINDOW TO DISPLAY THE SETTINGS
        self.running = running
        self.updateInstList()
        self.rows = int(self.rows)

        self.window = tk.Toplevel(self.gui.root)
        self.window.grab_set()
        self.window.wm_title('Edit Single Measurement')
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW",
                            self.accept)  # if they delete the window, assume they liked their settings
        self.instBoxes = []  # Keep track of the combobox widgets
        self.paramBoxes = []
        self.selInstsVar = []
        self.selParamsVar = []
        self.instTraces = []

        state = tk.DISABLED if self.running else tk.NORMAL
        self.addRow = tk.Button(self.window, text='...', command=self.createRow, width=50, state=state)
        self.addRow.grid(column=1, columnspan=4, row=self.rows + 1, sticky='NSEW')

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

        # generate the boxes for this row
        self.instBoxes.append(ttk.Combobox(self.window, textvariable=self.selInstsVar[ii], width=25, state=state))
        self.paramBoxes.append(ttk.Combobox(self.window, textvariable=self.selParamsVar[ii], width=25, state=state))
        self.instBoxes[ii]['values'] = self.stringInsts[:]
        if new:
            self.instBoxes[ii].current(0)
            self.selInstsVar[ii].set(self.stringInsts[0])
        else:
            try:
                self.instBoxes[ii].current(self.stringInsts.index(self.selInsts[ii]))
            except ValueError:
                self.instBoxes[ii].current(0)

        inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]
        params = [str(param) for param in inst.getQParams()]
        self.paramBoxes[ii]['values'] = params[:]
        if new:
            self.paramBoxes[ii].current(0)
        else:
            try:
                self.paramBoxes[ii].current(params.index(self.selParams[ii]))
            except ValueError:
                self.paramBoxes[ii].current(0)
        self.instBoxes[ii].grid(column=1, row=ii)
        self.paramBoxes[ii].grid(column=2, row=ii)

        if not self.running:
            self.instTraces.append(self.selInstsVar[ii].trace("w", lambda v, n, m, ii=ii: self.updateParams(v, n, m, ii)))

            # (re)build the control buttons
            self.addRow.destroy()
            self.subRows.append(tk.Button(self.window, text='X', activeforeground='red', command=lambda ii=ii: self.destroyRow(ii)))
            self.subRows[ii].grid(column=0, row=ii)
            self.addRow = tk.Button(self.window, text='...', command=self.createRow, width=50)
            self.addRow.grid(column=1, columnspan=4, row=ii + 1, sticky='NSEW')

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
           self.instBoxes[ii].grid(column=1, row=ii, sticky='NSEW')
           self.paramBoxes[ii].grid(column=2, row=ii, sticky='NSEW')

       self.addRow.destroy()
       self.addRow = tk.Button(self.window, text='...', command=self.createRow)
       self.addRow.grid(column=1, columnspan=3, row=self.rows, sticky='NSEW')

    def getMeasHeaders(self):
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
                for ii,comp in enumerate(param.comps):
                    if param.type == 'cont':
                        headers.append(sc.formatHeader(inst, comp, param.units[ii]))
                    else:
                        headers.append(sc.formatHeader(inst, comp))
        return headers

    def updateParams(self, v,n,m, ii):
       inst = self.instruments[self.stringInsts.index(self.selInstsVar[ii].get())]
       params = inst.getQParams()
       self.paramBoxes[ii]['values'] = params[:]
       self.paramBoxes[ii].current(0)