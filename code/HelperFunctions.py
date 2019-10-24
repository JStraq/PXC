#import tkinter as tk
import tkinter.messagebox as tkm
import re

def centerWindow(toplevel):
    toplevel.update_idletasks()
    w = toplevel.winfo_screenwidth()
    h = toplevel.winfo_screenheight()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    toplevel.geometry("+{}+{}".format(int(x), int(y)))
    
def noimp(self, *args):
        if len(args) > 0:
            args[0].destroy()
        tkm.showwarning('Nope', 'Function not implemented yet....blame Josh.')

def enumSequence(pos, title):
    return '{:02d}     {:s}'.format(pos, title)

def shortenParam(paramname):
    shortParam = paramname.replace(':', ' ')
    shortParam = shortParam.replace('--', ' ')
    shortParam = shortParam.split(' ')
    shortParam = shortParam[0] + ':' + shortParam[3]
    return shortParam

def getParamUnits(paramname):
    return paramname.split(' ')[1]

def plottable(params):
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
    title = step.title.split('   ')[1]
    title = '{:02d}     '.format(step.pos) + '     '*depth + title
    return title

def shortenLoop(title):
    title = re.search('(Loop [0-9]+):', title).group(1)
    return title