import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import FileHandlers as fh
import HelperFunctions as hf
from datetime import datetime
import multiprocessing as mp
import matplotlib.dates as mdates

import logging

class Plot:
    def __init__(self):

        self.xparam = None
        self.yparams = [None]
        self.xaxisname = ''
        self.yaxisname = ''
        self.yaxisunit = ''

        self.autox = True
        self.autoy1 = True
        self.autoy2 = True
        self.xlim = (0,1)
        self.ylim = (0,1)
        self.logx = False
        self.logy = False

        self.title = ''

        self.titlesize = 16
        self.labelsize = 14
        self.ticksize = 12

        self.alldata = [([],[])]

        self.maxpoints = 2000
        self.filtervars = []
        self.filterlims = []

        self.selectedColors = ['blue']
        self.selectedLines = ['-']
        self.selectedMarkers = ['.']
        self.onRightAx = [False]

        self.rows = 1
        self.columns = 1
        self.isSetup = False

class PlotManager:
    def __init__(self, master, row, col, exp, fileReqQ):
        self.log = logging.getLogger(__name__)
        self.plotfile = 'None selected'
        self.exp = exp
        self.fileReqQ = fileReqQ
        self.master = master
        self.plotbook = ttk.Notebook(self.master)
        self.plotbook.grid(row=row, column=col, sticky='NSEW', padx=10, pady=10)
        self.plottabs = [tk.Frame(self.plotbook)]
        self.availQuants = []

        self.figures = [Figure(figsize=(7, 7), dpi=75)]
        self.subplots = [self.figures[0].add_subplot(111)]
        self.twinaxes = [None]

        self.plotCanvases = [FigureCanvasTkAgg(self.figures[0], self.plottabs[0])]
        self.plotCanvases[0].draw()
        self.plotCanvases[0].get_tk_widget().grid(row=1, column=0, sticky='NSEW', columnspan=2)
        self.plots = [Plot()]

        self.plotbook.add(self.plottabs[0], text='Plot 1')

        self.toolbar_frames = [
            tk.Frame(self.plottabs[0], width=550, height=34)]  # exact height to prevent weirdness on mouseover
        self.toolbar_frames[0].grid(row=0, column=0, sticky='NSW')
        self.toolbars = [NavigationToolbar2Tk(self.plotCanvases[0], self.toolbar_frames[0])]

        self.plottabs[0].grid_rowconfigure(0, weight=0)
        self.plottabs[0].grid_rowconfigure(1, weight=1)
        self.plottabs[0].grid_columnconfigure(0, weight=1)

        self.defaultColors = ['blue', 'orange', 'green', 'red', 'purple',
                              'brown', 'pink', 'grey', 'yellow', 'cyan']
        self.colorRGBs =  ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                           '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

        self.defaultLines = ['-', '-.', '--', ':', 'none']
        self.defaultMarkers = ['.', '+', 'o','*', 'None']
        self.defaultLineWidth = 3
        self.defaultMarkerSize = 10

    def clearPlots(self):
        for ii,subplot in enumerate(self.subplots):
            subplot.clear()
            self.plots[ii].alldata = [([],[]) for y in self.plots[ii].yparams]
            self.plotCanvases[ii].show()

    def changePlotSettings(self):
        self.log.info('Change Plot Settings:')
        index = 0

        self.window = tk.Toplevel(self.master)
        self.window.wm_title('Edit Plot {:d}'.format(index+1))
        self.window.protocol("WM_DELETE_WINDOW",
                             self.savePlotSettings)  # if they delete the window, assume they liked their settings
        self.window.grab_set()

        tk.Label(self.window, text='Data File:').grid(row=0, column=0, sticky='NSE', padx=5)
        self.pathLabel = tk.Label(self.window, text=self.plotfile)
        self.pathLabel.grid(row=0, column=1, columnspan=3, sticky='NSW')
        self.changePath = tk.Button(self.window, text='Edit', command=self.chooseDataFile)
        self.changePath.grid(row=0, column=4, columnspan=2, sticky='NSE')

        self.paramFrame = tk.Frame(self.window)
        self.paramFrame.grid(row=1, column=0, columnspan=6, sticky='NSEW')
        tk.Label(self.paramFrame, text='X Axis:').grid(row=0, column=0, sticky='NSE')
        tk.Label(self.paramFrame, text='Y Axis:').grid(row=1, column=0, sticky='NSE')
        tk.Label(self.paramFrame, text='Y2?').grid(row=0, column=2, sticky='NSE')
        tk.Label(self.paramFrame, text='Color').grid(row=0, column=3, sticky='NSEW')
        tk.Label(self.paramFrame, text='Line').grid(row=0, column=4, sticky='NSEW')
        tk.Label(self.paramFrame, text='Marker').grid(row=0, column=5, sticky='NSEW')

        self.xaxisVar = tk.StringVar()
        self.yaxisVars = []
        self.yaxisSelects = []
        self.yaxSelVars = []
        self.yaxisBoxes = []
        self.yaxisDels = []
        self.yaxColors = []
        self.yaxColorVars = []
        self.yaxLines = []
        self.yaxLineVars = []
        self.yaxMarkers = []
        self.yaxMarkerVars = []

        self.xaxisBox = ttk.Combobox(self.paramFrame, textvariable=self.xaxisVar,width=50)
        self.xaxisBox.grid(row=0, column=1, sticky='NSEW')
        self.addYPButton = tk.Button(self.paramFrame, text='...', command=self.createRow)

        for yparam in self.plots[0].yparams:
            self.createRow()

        if self.plotfile != 'None selected':
            self.xaxisBox['values'] = self.availQuants
            self.yaxisBoxes[0]['values'] = self.availQuants

        if self.plots[0].xparam is not None:
            self.xaxisVar.set(self.plots[0].xparam)
            self.yaxisVars[0].set(self.plots[0].yparams[0])
        else:
            try:
                self.xaxisBox.current(0)
                self.yaxisBoxes[0].current(0)
            except:
                pass

        tk.Label(self.window, text='Autoscale X:').grid(row=2, column=0, sticky='NSE')
        tk.Label(self.window, text='Autoscale Y1:').grid(row=2, column=2, sticky='NSE')
        tk.Label(self.window, text='Autoscale Y2:').grid(row=2, column=4, sticky='NSE')
        self.autoXVar = tk.BooleanVar()
        self.autoscaleX = ttk.Checkbutton(self.window, variable=self.autoXVar)
        self.autoscaleX.grid(row=2, column=1, sticky='NSEW')
        self.autoY1Var = tk.BooleanVar()
        self.autoscaleY1 = ttk.Checkbutton(self.window, variable=self.autoY1Var)
        self.autoscaleY1.grid(row=2, column=3, sticky='NSEW')
        self.autoY2Var = tk.BooleanVar()
        self.autoscaleY2 = ttk.Checkbutton(self.window, variable=self.autoY2Var)
        self.autoscaleY2.grid(row=2, column=5, sticky='NSEW')

        self.autoXVar.set(self.plots[0].autox)
        self.autoY1Var.set(self.plots[0].autoy1)
        self.autoY2Var.set(self.plots[0].autoy2)

        tk.Label(self.window, text='X limits').grid(row=3, column=0, columnspan=2, sticky='NSEW')
        tk.Label(self.window, text='Y1 limits').grid(row=3, column=2, columnspan=2, sticky='NSEW')
        tk.Label(self.window, text='Y2 limits').grid(row=3, column=4, columnspan=2, sticky='NSEW')

        self.xminVar = tk.StringVar()
        self.xmaxVar = tk.StringVar()
        self.y1minVar = tk.StringVar()
        self.y1maxVar = tk.StringVar()
        self.y2minVar = tk.StringVar()
        self.y2maxVar = tk.StringVar()

        self.xminBox = tk.Entry(self.window, textvariable=self.xminVar, width=10)
        self.xmaxBox = tk.Entry(self.window, textvariable=self.xmaxVar, width=10)
        self.y1minBox = tk.Entry(self.window, textvariable=self.y1minVar, width=10)
        self.y1maxBox = tk.Entry(self.window, textvariable=self.y1maxVar, width=10)
        self.y2minBox = tk.Entry(self.window, textvariable=self.y2minVar, width=10)
        self.y2maxBox = tk.Entry(self.window, textvariable=self.y2maxVar, width=10)

        self.xminBox.grid(row=4, column=0, sticky='NSEW')
        self.xmaxBox.grid(row=4, column=1, sticky='NSEW')
        self.y1minBox.grid(row=4, column=2, sticky='NSEW')
        self.y1maxBox.grid(row=4, column=3, sticky='NSEW')
        self.y2minBox.grid(row=4, column=4, sticky='NSEW')
        self.y2maxBox.grid(row=4, column=5, sticky='NSEW')

        xlims = self.subplots[index].get_xlim()
        y1lims = self.subplots[index].get_ylim()
        self.xminVar.set(xlims[0])
        self.xmaxVar.set(xlims[1])
        self.y1minVar.set(y1lims[0])
        self.y1maxVar.set(y1lims[1])
        if self.twinaxes[index] is not None:
            y2lims = self.twinaxes[index].get_ylim()
            self.y2minVar.set(y2lims[0])
            self.y2maxVar.set(y2lims[1])
        else:
            self.y1minVar.set(0)
            self.y1maxVar.set(1)

        self.paramFrame.grid_rowconfigure(0,weight=1)
        self.paramFrame.grid_rowconfigure(1, weight=1)
        self.paramFrame.grid_rowconfigure(2, weight=1)
        self.paramFrame.grid_columnconfigure(0, weight=0)
        self.paramFrame.grid_columnconfigure(1, weight=1)
        self.paramFrame.grid_columnconfigure(2, weight=0)
        self.paramFrame.grid_columnconfigure(3, weight=1)
        self.paramFrame.grid_columnconfigure(4, weight=1)
        self.paramFrame.grid_columnconfigure(5, weight=1)
        self.paramFrame.grid_columnconfigure(6, weight=0)

        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0,weight=0)
        self.window.grid_columnconfigure(1, weight=1)
        self.window.grid_columnconfigure(2, weight=1)
        self.window.grid_columnconfigure(3, weight=1)
        self.window.grid_columnconfigure(4, weight=0)


        hf.centerWindow(self.window)
        self.master.wait_window(self.window)
        
    def createRow(self):
        size = len(self.yaxisBoxes)
        if size is None:
            size = 0

        self.yaxisVars.append(tk.StringVar())
        self.yaxSelVars.append(tk.BooleanVar())
        self.yaxisBoxes.append(ttk.Combobox(self.paramFrame, textvariable=self.yaxisVars[-1], width=50))
        self.yaxisBoxes[-1].grid(row=size+1, column=1, sticky='NSEW')
        self.yaxisBoxes[-1]['values'] = self.availQuants
        if size>0:
            self.yaxisDels.append(tk.Button(self.paramFrame, text='X', command=lambda x=size: self.deleteRow(x)))
            self.yaxisDels[-1].grid(row=size+1, column=6, sticky='NSEW')
        try:
            if len(self.plots[0].yparams)>=size-1:
                if self.plots[0].yparams[size] is not None:
                    self.yaxisBoxes[-1].current(self.availQuants.index(self.plots[0].yparams[size]))
            else:
                self.yaxisBoxes[-1].current(0)
        except (ValueError, IndexError):
            self.yaxisBoxes[-1].current(0)
        self.yaxisSelects.append(ttk.Checkbutton(self.paramFrame, variable=self.yaxSelVars[size]))
        self.yaxisSelects[-1].grid(row=size+1, column=2, sticky='NSEW')
        if size<len(self.plots[0].onRightAx):
            self.yaxSelVars[-1].set(self.plots[0].onRightAx[size])

        # Line styles
        self.yaxColorVars.append(tk.StringVar())
        self.yaxColors.append(ttk.Combobox(self.paramFrame, textvariable=self.yaxColorVars[-1], width=10))

        self.yaxColorVars[-1].set(self.defaultColors[size%len(self.defaultColors)])

        self.yaxLineVars.append(tk.StringVar())
        self.yaxLines.append(ttk.Combobox(self.paramFrame, textvariable=self.yaxLineVars[-1], width=5))
        self.yaxLineVars[-1].set(self.defaultLines[size % len(self.defaultLines)])

        self.yaxMarkerVars.append(tk.StringVar())
        self.yaxMarkers.append(ttk.Combobox(self.paramFrame, textvariable=self.yaxMarkerVars[-1], width=5))
        self.yaxMarkerVars[-1].set(self.defaultMarkers[size % len(self.defaultMarkers)])

        self.yaxColors[-1]['values'] = self.defaultColors
        self.yaxMarkers[-1]['values'] = self.defaultMarkers
        self.yaxLines[-1]['values'] = self.defaultLines

        if size < len(self.plots[0].selectedColors):
            self.yaxColorVars[-1].set(self.plots[0].selectedColors[size])
            self.yaxMarkerVars[-1].set(self.plots[0].selectedMarkers[size])
            self.yaxLineVars[-1].set(self.plots[0].selectedLines[size])
        else:
            self.yaxColors[-1].current(size%len(self.defaultColors))
            self.yaxMarkers[-1].current(0)
            self.yaxLines[-1].current(0)

        self.yaxColors[-1].grid(row=size+1, column=3, sticky='NSEW')
        self.yaxLines[-1].grid(row=size+1, column=4, sticky='NSEW')
        self.yaxMarkers[-1].grid(row=size+1, column=5, sticky='NSEW')

        self.addYPButton.grid(row=size+2, column=1,sticky='NSEW')
        self.paramFrame.grid_rowconfigure(size+2, weight=1)

    def deleteRow(self, row):
        self.yaxisSelects[row].destroy()
        self.yaxisBoxes[row].destroy()
        self.yaxisDels[-1].destroy()
        self.yaxColors[row].destroy()
        self.yaxLines[row].destroy()
        self.yaxMarkers[row].destroy()

        del self.yaxisVars[row]
        del self.yaxSelVars[row]
        del self.yaxisSelects[row]
        del self.yaxisBoxes[row]
        del self.yaxisDels[-1]

        del self.yaxColors[row]
        del self.yaxColorVars[row]
        del self.yaxLines[row]
        del self.yaxLineVars[row]
        del self.yaxMarkers[row]
        del self.yaxMarkerVars[row]

        for ii in range(1, len(self.yaxisBoxes)):
            self.yaxisBoxes[ii].grid(row=ii+1, column=1, sticky='NSEW')
            self.yaxisSelects[ii].grid(row=ii+1, column=2, sticky='NSEW')
            self.yaxColors[ii].grid(row=ii+1, column=3, sticky='NSEW')
            self.yaxLines[ii].grid(row=ii+1, column=4, sticky='NSEW')
            self.yaxMarkers[ii].grid(row=ii+1, column=5, sticky='NSEW')

        size = len(self.yaxisBoxes)
        self.addYPButton.grid(row=size + 2, column=1, sticky='NSEW')

    def savePlotSettings(self):
        self.plots[0].xparam = self.xaxisBox.get()
        self.plots[0].yparams = [yb.get() for yb in self.yaxisBoxes]
        self.plotfile = self.pathLabel['text']
        self.plots[0].onRightAx = [sv.get() for sv in self.yaxSelVars]

        self.plots[0].selectedColors = [c.get() for c in self.yaxColorVars]
        self.plots[0].selectedLines = [l.get() for l in self.yaxLineVars]
        self.plots[0].selectedMarkers = [m.get() for m in self.yaxMarkerVars]

        self.plots[0].autox = self.autoXVar.get()
        self.plots[0].autoy1 = self.autoY1Var.get()
        self.plots[0].autoy2 = self.autoY2Var.get()

        self.plots[0].isSetup = True
        self.updatePlots(newSettings=True)
        self.window.destroy()
        
        self.log.info(str(self.plots[0].__dict__))

    def chooseDataFile(self):
        self.plotFileName = filedialog.askopenfilename(filetypes=(("Data Files", "*.dat"), ("All files", "*.*")))
        if self.plotFileName is not '':
            self.pathLabel['text'] = self.plotFileName

            if not self.exp.isFileOpen():
                self.exp.openFile()
                fileproc = mp.Process(target=fh.fileHandler, args=[(self.exp, self.fileReqQ)])
                fileproc.start()

            self.fileReqQ.put(fh.fileRequest('Open File', args=self.plotFileName))
            self.fileReqQ.join()
            self.availQuants = hf.plottable(self.exp.get_fileAns())
            self.xaxisBox['state'] = 'normal'
            self.yaxisBoxes[0]['state'] = 'normal'
            self.xaxisBox['values'] = self.availQuants
            if self.xaxisVar.get() not in self.availQuants:
                self.xaxisBox.current(0)
            for ii, yaB in enumerate(self.yaxisBoxes):
                yaB['values'] = self.availQuants
                if self.yaxisVars[ii] not in self.availQuants:
                    self.yaxisBoxes[ii].current(0)

    def addTab(self):
        pass

    def delTab(self):
        pass

    def updatePlots(self, newSettings=False):
        self.log.info('Updating Plots')
        if self.plots[0].isSetup:
            if not self.plots[0].autox:
                xlim = self.subplots[0].get_xlim()
            if not self.plots[0].autoy1:
                y1lim = self.subplots[0].get_ylim()
            if not self.plots[0].autoy2:
                if self.twinaxes[0] is not None:
                    y2lim = self.subplots[0].get_ylim()


            if True in self.plots[0].onRightAx:
                if self.twinaxes[0] is None:
                    self.twinaxes[0] = self.subplots[0].twinx()
            if self.plots[0].xparam is not '':
                if not self.exp.isFileOpen():
                    self.exp.openFile()
                    fileproc = mp.Process(target=fh.fileHandler, args=[(self.exp, self.fileReqQ)])
                    fileproc.start()
                index = self.plotbook.index(self.plotbook.select())
                if newSettings or len(self.plots[index].alldata[index][0]) > 2000:  # reread entire file to refresh the data to match the new settings

                    self.fileReqQ.put(fh.fileRequest('Read All', args=(self.plots[index].xparam, self.plots[index].yparams)))
                    self.fileReqQ.join()

                    try:
                        self.plots[0].alldata = self.exp.get_fileAns()
                    except TypeError:
                        self.plots[0].alldata = [([],[])]

                else:  # just read whatever is in the unread buffer
                    self.fileReqQ.put(fh.fileRequest('Read Unread', args=(self.plots[index].xparam, self.plots[index].yparams)))
                    self.fileReqQ.join()
                    unread = self.exp.get_fileAns()

                    if unread is not None and self.plots[0].xparam is not None and self.plots[0].yparams[0] is not None:
                        if len(unread)>0:
                            for record in unread:
                                keys = list(record.keys())
                                for ii, yp in enumerate(self.plots[0].yparams):
                                    if yp in keys:
                                        try:
                                            if record[self.plots[0].xparam] is not '-' and record[yp] is not '-':
                                                if self.plots[0].xparam == 'Timestamp':
                                                    try:
                                                        record[self.plots[0].xparam] = datetime.strptime(record[self.plots[0].xparam], '%Y-%m-%d %H:%M:%S.%f')
                                                    except TypeError:
                                                        pass
                                                if yp == 'Timestamp':
                                                    try:
                                                        record[yp] = datetime.strptime(record[yp], '%Y-%m-%d %H:%M:%S.%f')
                                                    except TypeError:
                                                        pass
                                                self.plots[0].alldata[ii][0].append(record[self.plots[0].xparam])
                                                self.plots[0].alldata[ii][1].append(record[yp])
                                        except KeyError:
                                            pass

                self.subplots[index].clear()
                if self.twinaxes[index] is not None:
                    self.twinaxes[index].clear()
                nright = 0
                nleft = 0
                rightparams = []
                leftparams = []
                if self.plots[0].alldata is not None:
                    for ii, ad in enumerate(self.plots[0].alldata):
                        xx, yy = ad
                        if self.plots[0].onRightAx[ii]:
                            nright += 1
                            rightparams.append(self.plots[0].yparams[ii])
                            self.twinaxes[index].plot(xx,yy, linewidth=self.defaultLineWidth,
                                                      linestyle=self.plots[0].selectedLines[ii],
                                                      color=self.colorRGBs[self.defaultColors.index(self.plots[0].selectedColors[ii])],
                                                      marker = self.plots[0].selectedMarkers[ii],
                                                      markersize = self.defaultMarkerSize,
                                                      label=hf.shortenParam(self.plots[0].yparams[ii]) + ' (R)')
                            self.subplots[index].plot([], linewidth=self.defaultLineWidth,
                                                      linestyle=self.plots[0].selectedLines[ii],
                                                      color=self.colorRGBs[self.defaultColors.index(self.plots[0].selectedColors[ii])],
                                                      marker = self.plots[0].selectedMarkers[ii],
                                                      markersize = self.defaultMarkerSize,
                                                      label=hf.shortenParam(self.plots[0].yparams[ii])+' (R)')
                        else:
                            nleft += 1
                            leftparams.append(self.plots[0].yparams[ii])
                            self.subplots[index].plot(xx, yy, linewidth=self.defaultLineWidth,
                                                      linestyle=self.plots[0].selectedLines[ii],
                                                      color=self.colorRGBs[self.defaultColors.index(self.plots[0].selectedColors[ii])],
                                                      marker=self.plots[0].selectedMarkers[ii],
                                                      markersize=self.defaultMarkerSize,
                                                      label=hf.shortenParam(self.plots[0].yparams[ii]))
                            if self.twinaxes[index] is not None:
                                self.twinaxes[index].plot([], linewidth=self.defaultLineWidth,
                                                          linestyle=self.plots[0].selectedLines[ii],
                                                          color=self.colorRGBs[
                                                              self.defaultColors.index(self.plots[0].selectedColors[ii])],
                                                          marker=self.plots[0].selectedMarkers[ii],
                                                          markersize=self.defaultMarkerSize,
                                                          label=hf.shortenParam(self.plots[0].yparams[ii]))

                    # Manual Scaling?
                    if not self.plots[0].autox:
                        self.subplots[0].set_xlim(xlim)
                    if not self.plots[0].autoy1:
                        self.subplots[0].set_ylim(y1lim)
                    if not self.plots[0].autoy2:
                        if self.twinaxes[0] is not None:
                            self.twinaxes[0].set_ylim(y2lim)

                    # Get everything labeled
                    if nright+nleft > 1:
                        if nright>0:
                            self.twinaxes[index].legend()
                        else:
                            self.subplots[index].legend()
                    self.subplots[index].set_xlabel(self.plots[0].xparam, fontsize=self.plots[0].labelsize)

                    # Format timestamp axes
                    if self.plots[0].xparam == 'Timestamp':
                        self.subplots[index].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
                        for tick in self.subplots[index].get_xticklabels():
                            tick.set_rotation(45)

                    if nleft == 1:
                        self.subplots[index].set_ylabel(leftparams[0], fontsize=self.plots[0].labelsize)
                    elif nleft > 1:
                        units = [hf.getParamUnits(yp)for yp in leftparams]
                        if len(list(set(units)))==1:
                            self.subplots[index].set_ylabel(units[0], fontsize=self.plots[0].labelsize)
                        else:
                            self.subplots[index].set_ylabel(', '.join(set(units)), fontsize=self.plots[0].labelsize)

                    if nright == 1:
                        self.twinaxes[index].set_ylabel(rightparams[0], fontsize=self.plots[0].labelsize)
                    elif nright > 1:
                        units = [hf.getParamUnits(yp) for yp in leftparams]
                        if len(list(set(units))) == 1:
                            self.twinaxes[index].set_ylabel(units[0], fontsize=self.plots[0].labelsize)
                        else:
                            self.twinaxes[index].set_ylabel(', '.join(set(units)), fontsize=self.plots[0].labelsize)
                    self.figures[index].tight_layout()
                    self.plotCanvases[index].show()                
                        