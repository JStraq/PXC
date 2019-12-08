import tkinter as tk
from tkinter import ttk
from . import SeqCommand as sc
import HelperFunctions as hf


class SetCmd(sc.SeqCmd):
    """
    Change an arbitrary number of settings or execute simple commands
    
    Parameters
    ----------
    exp : ExpController
    app : Apparatus
    pos : int
        Numerical position in the sequence, starting from zero.
    dup : boolean
        Flag for whether or not to open the configuration window:\
        for a brand new sequence command, we need to open it.  If \
        we're just copying an old one, we don't.
    gui : ExpGUI
        A link to the GUI: this is set whenever the sequence is active, \
        and equal to ``None`` if the command is being saved to a sequence file.

    Attributes
    ----------
    rows : int
        number of parameters to be interrogated (default 0)
    selParams : list of Param
        ordered list of the parameters to be edited
    selInsts : list of Instrument
        ordered list of the instruments to be edited
    selVars : list
        New values to set for each command
    """
    cmdname = 'Change Settings'
    def __init__(self, exp, app, pos=None, dup=False, gui=None):
        sc.SeqCmd.__init__(self, exp=exp, app=app, pos=pos, dup=dup, gui=gui)
        self.status = ['Status:\tSetting Values', 'Instrument:\t', 'Parameter:\t']
        self.type = 'SetCommand'
        self.rows = 0

        # Parameters to execute commands
        self.selInsts = []  # run on this instrument
        self.selParams = []  # and set this parameter
        self.selVals = []  # to this value
        self.rowheight = 30

        self.actualInsts = []

        self.title = 'Set'
        if not dup:
            self.edit()
    
    
    def accept(self):
        """
        If the window is closed, destroy widgets on the window and save\
        all the settings into the instance variables.
        """

        # save the settings
        self.selInsts = [x.get() for x in self.selInstsVar]
        self.actualInsts = [self.instruments[self.stringInsts.index(x)] for x in self.selInsts]
        self.selParams = [x.get() for x in self.selParamsVar]
        self.selVals = [x.get() for x in self.selValsVar]

        # clear the tk specific variables
        self.selInstsVar = []
        self.selParamsVar = []
        self.selValsVar = []
        self.valUnitsVar = []
        self.itraces = []
        self.ptraces = []
        
        self.updateTitle()

        #clear more tk lists
        self.instBoxes = []
        self.paramBoxes = []
        self.valBoxes = []
        self.valLabels = []
        self.subRows = []
        self.addRow = None
        
        self.window.grab_release()
        self.window.destroy()


    def updateTitle(self):
        """
        Give the sequence command a more descriptive name based on its contents
        """
        if len(self.selParams) == 0:
            self.title = 'Set (Nothing)'
        elif len(self.selParams) == 1:
            self.title = 'Set {:s}'.format(self.selParams[0])
        elif len(self.selParams) == 2:
            self.title = 'Set {:s}, {:s}'.format(self.selParams[0], self.selParams[1])
        else:
            self.title = 'Set {:s}, {:s}, ...'.format(self.selParams[0],self.selParams[1])
        self.title = hf.enumSequence(self.pos, self.title)


    def edit(self, running=False):
        """
        Open a window to edit the settings
        
        Parameters
        ----------
        running : boolean
            only allow changes if a sequence is not running
        """
        self.instruments = []
        for inst in self.app.instList:
            if inst.name is not None:
                self.instruments.append(inst)
        self.stringInsts = [str(inst) for inst in self.instruments]
        self.running = running

        self.actualInsts = []
        self.window = tk.Toplevel(self.gui.root)
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        
        self.window.wm_title('Edit Set Command')
        self.window.protocol("WM_DELETE_WINDOW",
                             self.accept)  # if they delete the window, assume they liked their settings
        tk.Label(self.window, text='Instrument').grid(column=1, row=0, sticky='NSEW', padx=5)
        tk.Label(self.window, text='Parameter').grid(column=2, row=0, sticky='NSEW', padx=5)
        tk.Label(self.window, text='Value').grid(column=3, row=0, sticky='NSEW', padx=5)

        # These store the objects which appear on the window
        self.instBoxes = []
        self.paramBoxes = []
        self.valBoxes = []
        self.valLabels = []

        # Variables to make passing things around the gui easier
        self.selInstsVar = []
        self.selParamsVar = []
        self.selValsVar = []
        self.valUnitsVar = []
        self.itraces = []
        self.ptraces = []

        if not self.running:
            self.addRow = tk.Button(self.window, text='...', command=self.createRow)
            self.addRow.grid(column=1, columnspan=3, row=self.rows + 1, sticky='NSEW')
            self.subRows = []

        for ii in range(0, self.rows):  # how many commands are added here? (default 0 for first edit)
            self.createRow(new=False)
        hf.centerWindow(self.window)
        self.updateSize()
        self.gui.root.wait_window(self.window)


    def updateSize(self):
        """
        Make sure the edit dialog is large enough to accommodate its content
        """
        rowpx = self.rowheight*(self.rows+2)
        self.window.geometry('{:d}x{:d}'.format(600,rowpx))
        for ii in range(self.rows+2):
            self.window.grid_rowconfigure(ii, weight=0, minsize=self.rowheight)
        for ii in range(1,4):
            self.window.grid_columnconfigure(ii, weight=1, minsize=20)
        self.window.grid_columnconfigure(0,weight=0,minsize=1)
        self.window.grid_columnconfigure(4,weight=0,minsize=20)    
            

    def updateOptions(self, v, n, m, ii, level):
        """
        When the user picks a different instrument or parameter, change other downstream inputs
        to accommodate valid responses.
        
        Parameters
        ----------
        ii : int
            row number under consideration
        level : string
            This one function handles both instrument level changes (where\
            it updates the list of possible parameters) as well as parameter\
            level changes, where it sets up the GUI to take the proper type
            of input.  Which one is relevant is set by ``level='inst'`` or ``'param'``.
        """
        if level == 'inst':  # user selected a new isntrument
            try:
                newInst = self.instruments[self.stringInsts.index(self.instBoxes[ii].get())]
            except ValueError:  # the user tried to do something stupid.
                newInst = self.instBoxes[ii]['values'][0]
                return None
            if self.actualInsts[ii] != newInst:  # i.e. an ACTUAL change occured, the user wasn't just poking around
                self.actualInsts[ii] = newInst
                self.paramBoxes[ii]['values'] = newInst.getWParams()[:]
                self.paramBoxes[ii].current(0)

        elif level == 'param':   # user selected a new parameter
            param = self.actualInsts[ii].getParam(self.paramBoxes[ii].get())
            if param.type == 'disc':
                labeledVals = ["{:s} ({:s})".format(param.labels[ii], param.vals[ii]) for ii in range(len(param.vals))]
            if (type(self.valBoxes[ii]) == tk.Entry and param.type == 'cont'):
                pass  # we're still talking about continuous variables:leave it as it is.
            elif (type(self.valBoxes[ii]) == ttk.Combobox and param.type == 'disc'):  # always was, still is combobox.
                if self.valBoxes[ii]['values'] == param.vals:
                    pass  # same combobox: keep the same value, make no changes
                else:  # shake things up
                    self.valBoxes[ii].current(0)
                    self.valBoxes[ii]['values'] = labeledVals
                    self.valBoxes[ii].current(0)
            else:  # we're going to have to change something
                if self.valBoxes[ii] is not None:  # As long as there's SOMETHING there
                    self.valBoxes[ii].destroy()  # then we'll have to delete it
                if param.type == 'cont':  # then we'll create an input box of the right type
                    self.valBoxes[ii] = tk.Entry(self.window, textvariable=self.selValsVar[ii])
                    self.valBoxes[ii].grid(column=3, row=ii + 1, sticky='NSEW')
                    self.valBoxes[ii].bind('<FocusOut>', lambda event: self.protectValue(event, ii=ii))
                    self.protectValue(None, ii)
                elif param.type == 'disc':
                    self.valBoxes[ii] = (ttk.Combobox(self.window, textvariable=self.selValsVar[ii]))
                    self.valBoxes[ii]['values'] = labeledVals
                    self.valBoxes[ii].current(0)
                    self.valBoxes[ii].grid(column=3, row=ii + 1, sticky='NSEW')
                else:
                    self.valBoxes[ii] = None
            self.valUnitsVar[ii].set(param.units)


    def createRow(self, new=True):
        """
        Generate a new set of boxes on the GUI window
        Parameters
        ----------
        new : boolean
            If the user created a new one, guess what to use.  Otherwise,
            it already exists and we should just use whatever is already there.
        """
        if new:
            ii = int(self.rows)
            self.rows += 1
        else:
            ii = len(self.instBoxes)  # this is for regenerating the edit window when there's already data

        # generate new variables
        self.selInstsVar.append(tk.StringVar())  # create variables to store the user's selections
        self.selParamsVar.append(tk.StringVar())
        self.selValsVar.append(tk.StringVar())
        self.valUnitsVar.append(tk.StringVar())

        # generate the boxes for this row
        state = tk.DISABLED if self.running else tk.NORMAL
        self.instBoxes.append(ttk.Combobox(self.window, textvariable=self.selInstsVar[ii], state=state))
        self.instBoxes[ii]['values'] = self.stringInsts[:]
        if new:
            self.instBoxes[ii].current(0)
        else:
            try:
                self.instBoxes[ii].current(self.stringInsts.index(self.selInsts[ii]))
            except ValueError:
                self.instBoxes[ii].current(0)
        self.instBoxes[ii].grid(column=1, row=ii + 1, sticky='NSEW')
        self.actualInsts.append(self.instruments[self.stringInsts.index(self.instBoxes[ii].get())])

        self.paramBoxes.append(ttk.Combobox(self.window, textvariable=self.selParamsVar[ii], state=state))
        self.paramBoxes[ii]['values'] = self.actualInsts[ii].getWParams()[:]
        if new:
            self.paramBoxes[ii].current(0)
        else:
            try:
                self.paramBoxes[ii].current(self.paramBoxes[ii]['values'].index(self.selParams[ii]))
            except ValueError:
                self.paramBoxes[ii].current(0)
        self.paramBoxes[ii].grid(column=2, row=ii + 1, sticky='NSEW')

        # depending on the parameter type chosen by default, you'll need different types of value boxes
        param = self.actualInsts[ii].getParam(self.paramBoxes[ii].get())
        if param.type != 'act':
            if param.type == 'disc':
                self.valBoxes.append(ttk.Combobox(self.window, textvariable=self.selValsVar[ii], state=state))
                labeledVals = ["{:s} ({:s})".format(param.labels[ii], param.vals[ii]) for ii in
                               range(len(param.vals))]
                self.valBoxes[ii]['values'] = labeledVals
                if new:
                    self.valBoxes[ii].current(0)
                else:
                    try:
                        self.valBoxes[ii].current(labeledVals.index(self.selVals[ii]))
                    except ValueError:
                        self.valBoxes[ii].current(0)
            elif param.type == 'cont':
                self.valBoxes.append(tk.Entry(self.window, textvariable=self.selValsVar[ii], state=state))
                self.valBoxes[ii].insert(0, self.selValsVar[ii].get())
                self.valBoxes[ii].bind('<FocusOut>', lambda event: self.protectValue(event, ii=ii))
                if ii<len(self.selVals):
                    self.selValsVar[ii].set(self.selVals[ii])
                self.protectValue(None, ii)
            self.valBoxes[ii].grid(column=3, row=ii + 1, sticky='NSEW')
        else:
            self.valBoxes.append(None)

        # When relevant, show the user what units they'll be working in
        self.valUnitsVar[ii].set(param.units)
        self.valLabels.append(tk.Label(self.window, textvariable=self.valUnitsVar[ii]))
        self.valLabels[ii].grid(column=4, row=ii + 1, sticky='NSW')

        # move and rebuild the control buttons
        if not self.running:
            self.addRow.destroy()
            self.subRows.append(tk.Button(self.window, text='X', activeforeground='red', command=lambda ii=ii: self.destroyRow(ii)))
            self.subRows[ii].grid(column=0, row=ii+1, sticky='NSEW')
            self.addRow = tk.Button(self.window, text='...', command=self.createRow)
            self.addRow.grid(column=1, columnspan=3, row=ii + 2, sticky='NSEW')
            self.itraces.append(
                self.selInstsVar[ii].trace("w", lambda v, n, m, ii=ii: self.updateOptions(v, n, m, ii, 'inst')))
            self.ptraces.append(
                self.selParamsVar[ii].trace("w", lambda v, n, m, ii=ii: self.updateOptions(v, n, m, ii, 'param')))

        self.updateSize()
        

    def protectValue(self, event, ii):
        """
        Coerce the user's input value into the range of reasonable values
        for the given parameter.
        
        Parameters
        ----------
        event : tuple
            This argument is unused, but the tk trace which triggers this
            event sends it by default anyway.
        ii : int
            Which row to check and coerce.
        
        """
        try:
            param = self.actualInsts[ii].getParam(self.paramBoxes[ii].get())
    
            vals = self.selValsVar[ii].get().split(',')  # in the event of multiple arguments, treat them separately
            newvals = []
            for val in vals:
                try:
                    val = val.strip(' \t\n\r')
                    fval = float(val)
                except ValueError:
                    fval = 0.0
                fmtstring = '{:f}'
                if param.prec is not None:
                    fval = round(fval, param.prec)
                    fmtstring = '{{:.{:d}f}}'.format(
                        param.prec)  # I hate this... but I don't know how else to dynamically format
                if param.pmax is not None:  # the string with the proper precision...
                    fval = param.pmax if fval > param.pmax else fval
                if param.pmin is not None:
                    fval = param.pmin if fval < param.pmin else fval
                newvals.append(fmtstring.format(fval))
                    
            pvals = ",".join(newvals)
            self.selValsVar[ii].set(pvals)
        except IndexError:
            pass


    def destroyRow(self, ii):
        """
        hitting the little 'X' button to the left removes that row and all its data.
        
        Parameters
        ----------
        ii : int
            Which row to edit
        """
        self.rows -= 1

        # carefully strip the callbacks to we don't trigger from or to dead buttons
        self.selInstsVar[ii].trace_vdelete("w", self.itraces[ii])
        del self.itraces[ii]
        self.selParamsVar[ii].trace_vdelete("w", self.ptraces[ii])
        del self.ptraces[ii]

        # clear the actual boxes and labels themselves
        self.instBoxes[ii].destroy()
        del self.instBoxes[ii]
        self.paramBoxes[ii].destroy()
        del self.paramBoxes[ii]
        if self.valBoxes[ii] is not None:
            self.valBoxes[ii].destroy()
        del self.valBoxes[ii]
        self.valLabels[ii].destroy()
        del self.valLabels[ii]
        del self.selInstsVar[ii]
        del self.selParamsVar[ii]
        del self.selValsVar[ii]
        del self.valUnitsVar[ii]

        # move and rebuild the control buttons
        self.subRows[-1].destroy()
        del self.subRows[-1]

        for ii in range(len(self.instBoxes)):
            self.instBoxes[ii].grid_forget()
            self.paramBoxes[ii].grid_forget()
            self.instBoxes[ii].grid(column=1, row=ii+1, sticky='NSEW')
            self.paramBoxes[ii].grid(column=2, row=ii+1, sticky='NSEW')
            if self.valBoxes[ii] is not None:
                self.valBoxes[ii].grid_forget()
                self.valBoxes[ii].grid(column=3, row=ii+1, sticky='NSEW')
            if self.valLabels[ii] is not None:
                self.valLabels[ii].grid_forget()
                self.valLabels[ii].grid(column=4, row=ii+1, sticky='NSW')
        self.addRow.destroy()
        self.addRow = tk.Button(self.window, text='...', command=self.createRow)
        self.addRow.grid(column=1, columnspan=3, row=self.rows+1, sticky='NSEW')
        self.updateSize()        
        
        
    def execute(self, fileReqQ):
        """
        Write the selected values to the selected parameters on the selected instruments
        
        Parameters
        ----------
        fileReqQ : multiprocessing.Queue
            queue for sending data to the file (unused, but required for superclass)
        """
        self.stringInsts = [str(x) for x in self.instruments]
        if not self.exp.isAborted():            # if the sequence is still running
            self.actualInsts = [self.instruments[self.stringInsts.index(x)] for x in self.selInsts]
            for ii in range(len(self.selInsts)):  # cycle through the instruments selected
                param = self.actualInsts[ii].getParam(self.selParams[ii])  # get the reference to the param itself
                self.status[1] = 'Instrument:\t{:s}'.format(str(self.actualInsts[ii]))
                if self.selVals[ii] is not '':    # if a value has actually been set, and not left blank
                    if param.type == 'disc':
                        labeledVals = ["{:s} ({:s})".format(param.labels[ii], param.vals[ii]) for ii in
                                       range(len(param.vals))]  # regenerate the list of values paired with meanings
                        print(labeledVals)
                        val = param.vals[labeledVals.index(self.selVals[ii])]   # search it to get proper value
                        self.status[2] = 'Parameter:\t{:s} = {:s}'.format(str(param), self.selVals[ii])
                        self.exp.setStatus(self.status)
                        self.actualInsts[ii].writeParam(self.selParams[ii], val)  # actually write the thing
                    else:
                        self.status[2] = 'Parameter:\t{:s} = {:s} {:s}'.format(str(param), str(self.selVals[ii]), str(param.units))
                        self.exp.setStatus(self.status)
                        self.actualInsts[ii].writeParam(self.selParams[ii], self.selVals[ii])  # write it
                else:
                    if param.type == 'act':
                        self.status[2] = 'Parameter:\t{:s}'.format(str(param))
                        self.exp.setStatus(self.status)
                        self.actualInsts[ii].writeParam(self.selParams[ii])  # if it's an action, it won't need a value
                    else:
                        pass  # the user didn't supply a value, even though I asked for one.  Forget that clown.


    def getMeasHeaders(self):
        """
        Get list of headers to which this command can contribute data:
        always none for this type.
        
        Returns
        -------
        list
            an empty list literal
        """
        return []