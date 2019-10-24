import abc
import numpy as np


def formatHeader(inst, param, unit=None):  # take in strings, return standardized header
    text = "{:s}--{:s}".format(str(inst), str(param))
    if unit is not None:
        text = "{:s} ({:s})".format(text, unit)
    return text


class SeqCmd(metaclass=abc.ABCMeta):
    """
    Superclass for all different types of command steps
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
        self.instruments = []
        for inst in self.app.instList:
            if inst.name is not None:
                self.instruments.append(inst)
        self.stringInsts = [str(x) for x in self.instruments]
    
    def copy(self):
        """
        Makes a copy of the given object--this is somewhere between shallow and deep builtin copy
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
