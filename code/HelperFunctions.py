#import tkinter as tk
import tkinter.messagebox as tkm
import re


def centerWindow(toplevel):
    """
    Force a dialogbox to the center of the screen
    
    Parameters
    ----------
    toplevel : tk.TopLevel
        The dialog to center
    """
    toplevel.update_idletasks()
    w = toplevel.winfo_screenwidth()
    h = toplevel.winfo_screenheight()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    toplevel.geometry("+{}+{}".format(int(x), int(y)))
    

def noimp(self, *args):
    """
    Placeholder for unimplemented functions, especially GUI buttons
    """
    if len(args) > 0:
        args[0].destroy()
    tkm.showwarning('Nope', 'Function not implemented yet....')


def enumSequence(pos, title):
    """
    Standardized way of formatting strings and positions for sequence
    command titles.
    
    Parameters
    ----------
    pos : int
        Position within the sequence
    title : str
        title of the sequence step
    
    Returns
    -------
    str
        The updated string with a 2-digit, zero-padded int prepended.
    """
    return '{:02d}     {:s}'.format(pos, title)


def shortenParam(paramname):
    """
    Cut out extra text from a parameter name to make plot a bit prettier
    
    Parameters
    ----------
    paramname : str
        full parameter name
    
    Returns
    -------
    str
        The first and last bits of the name
    """
    if paramname == 'Timestamp':
        return paramname
    shortParam = paramname.replace(':', ' ')
    shortParam = shortParam.replace('--', ' ')
    shortParam = shortParam.split(' ')
    shortParam = shortParam[0] + ':' + shortParam[3]
    return shortParam


def getParamUnits(paramname):
    """
        Pull the units out of a parameter name
    """
    if paramname == 'Timestamp':
        return ''
    return paramname.split(' ')[1]

def plottable(params):
    """
    Ask whether or not a particular parameter should be plottable.
    The criterion here is whether or not it has units, i.e. that it is
    defined as a continuous parameter.  Timestamp is explicitly included too.
    Discrete parameters, while they can be recorded, are not intended for
    plotting--the required manipulations are too involved to be within
    scope for PXC.
    
    Parameter
    ---------
    params : list of str
        parameters pulled from the data file header
        
    Returns
    -------
    hasUnits : list of str
        only those which should show up as options for plotting.
    """
    hasUnits = []
    for p in params:
        try:
            if p=='Timestamp':
                hasUnits.append(p)
            else:
                getParamUnits(p)
                hasUnits.append(p)
        except IndexError:
            pass
    return hasUnits
    

def indentLoops(step, depth):
    """
    Format the titles in the sequence to make loops automatically nest
    inside of each other.
    
    Parameters
    ----------
    step : SeqCmd
        which step to indent
    depth : int
        how deep to indent it
        
    Returns
    -------
    title : str
        the new title with the enumeration
    """
    title = step.title.split('   ')[1]
    title = '{:02d}     '.format(step.pos) + '     '*depth + title
    return title


def shortenLoop(title):
    """
    Return a shorter version of the loop name
    
    Parameters
    ----------
    title : str
        title of the loop
    
    Returns
    title : str
        truncated title
    """
    title = re.search('(Loop [0-9]+):', title).group(1)
    return title