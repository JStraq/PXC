import abc
import numpy as np


def formatHeader(inst, param, unit=None):
    """
    Generalized function for how headers look in the datafile
    
    Parameters
    ----------
    inst : str
        name of the instrument
    param : str
        name of the parameter
    unit : str (optional)
        unit of the parameter
    
    Returns
    -------
    text : str
        A consistently formatted header string
    """
    text = "{:s}--{:s}".format(str(inst), str(param))
    if unit is not None:
        text = "{:s} ({:s})".format(text, unit)
    return text


class SeqCmd(metaclass=abc.ABCMeta):
    """
    Superclass for all different types of command steps

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
    title : str
        Human-readable title for this type of command (to be overridden\
        by subclass constructor)
    exp : ExpController
    pos : int
        position of this step within the sequence
    instruments : list of Instrument
        List of active instrument objects in this apparatus
    stringInsts : list of str
        list of human-readable strings describing the instruments,
        used in the configuration window
    status : str
        Text to display on the GUI while this command is executing (to \
        be overriden by subclass constructor)
    type : str
        Short string identifying the command type (to be overridden by \
        subclass constructor)
    enabled : boolean
        True if this command will execute with the rest of the sequence.
    app : Apparatus
    gui : ExpGUI
    
    """
    cmdname = 'UNNAMED COMMAND'
    def __init__(self, exp, app, pos=None, dup=False, gui=None):
        self.title = ""
        self.exp = exp
        self.pos = pos   # position in the sequence
        self.instruments = app.get_activeInsts()
        self.stringInsts = []
        self.status = 'BLANK COMMAND'  # output for the status indicator
        self.type = 'Blank'
        self.enabled = True
        self.app = app
        self.gui = gui


    def __str__(self):
        return self.title


    def __repr__(self):
        return self.title
    
    
    def updateInstList(self):
        """
        Rebuild the list of instruments as strings.  This is done by asking\
        the apparatus which instruments have been named.
        """
        self.instruments = []
        for inst in self.app.instList:
            if inst.name is not None:
                self.instruments.append(inst)
        self.stringInsts = [str(x) for x in self.instruments]
    
    
    def copy(self):
        """
        Makes a copy of the given object--this is somewhere between\
        shallow and deep builtin copy functions, in order to accommodate\
        the mishmash of different data types involved.
        
        Returns
        -------
        new : SeqCmd
            The new copy object
        """
        new = type(self)(self.exp, self.app, self.pos, dup=True, gui=self.gui)  # create one of the same type
        for key in self.__dict__:  # for every instance variable
            if isinstance(self.__dict__[key], list):  # if it's a list, then copy it by slicing
                new.__dict__[key] = self.__dict__[key][:]
            else:  # just normal assignment works fine
                new.__dict__[key] = self.__dict__[key]
        return new
    
    
    def description(self):
        """
        Generates a text description of the step object.
        All Tk specific variables or other temporary ones are set to None or [] by cmd.accept(),
        so this code ignores all such variables.
        
        Returns
        -------
        descriptor : str
            Human- and machine-readable description of this command.
        """
        ignoreList = ['status', 'title', 'pos', 'instruments',
                      'loop', 'iteration', 'exp', 'app', 'gui',
                      'window', 'running', 'stringInsts']
        
        descriptor = 'Sequence Command {:d}:\n'.format(self.pos)   # start the descriptor block with known opening
        for key in self.__dict__.keys():       # for every instance variable
            if key not in ignoreList:          # if it is an interesting one
                if isinstance(self.__dict__[key], list):   # if it's a list
                    if len(self.__dict__[key])>0:          # ignore it if it's empty
                        descriptor += '\t{:s} = {:s}\n'.format(str(key), str(self.__dict__[key]))
                elif isinstance(self.__dict__[key], np.ndarray):
                    if len(self.__dict__[key]) > 0:  # ignore it if it's empty
                        descriptor += '\t{:s} = {:s}\n'.format(str(key), str(list(self.__dict__[key])))
                else:
                    if self.__dict__[key] is not None:     # ignore ones which have been cleared, too
                        descriptor += '\t{:s} = {:s}\n'.format(str(key), str(self.__dict__[key]))
        return descriptor
