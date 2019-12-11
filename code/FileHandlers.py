import datetime
import numpy as np
import logging
import tzlocal


def fileHandler(args):
    print('init_files')
    exp, fileReqQ, logQ = args
    
    qh = logging.handlers.QueueHandler(logQ)
    logger = logging.getLogger('file')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)
    
    logger.info('Starting File Process')
    
    dbase = DataBase(logQ)
    fp_terminate = False
    
    while not exp.get_killFlag() and not fp_terminate:
        if not fileReqQ.empty():
            try:
                req = fileReqQ.get()
                logger.critical('###POP FILEQ: {:s}'.format(req.type))
            except EOFError as e:
                logger.info('FileReqQ has crashed',)
                logger.info(e)
            try:
                if req.type == 'Read Latest':
                    exp.set_fileLatest(req.execute(dbase))
                elif req.type == 'Terminate File Process':
                    fp_terminate = True
                    dbase.closefile()
                else:
                    exp.set_fileAns(req.execute(dbase))
            except Exception as e:
                logger.info('Unhandled exception happened in file process')
                logger.info('while processing {:s}-type fileRequest'.format(req.type))
                logger.info(e)
            fileReqQ.task_done()

    logger.info('file writing is finished')
    if dbase is not None:
        dbase.closefile()  # don't do drugs, close your files, stay in school
        logger.info('closed the data file')



class fileRequest:
    """
    Class for mediating requests from other processes to the file process\
    by sending not just string instructions but also measurement or \
    configuration data.
    
    Parameters
    ----------
    reqtype : str
        A human-readable name describing the requested action
    args : tuple
        Extra instructions, parameters, or data as required for the reqtype.
    
    """

    def __init__(self, reqtype, args=None):
        self.type = reqtype
        self.args = args


    def execute(self, dbase):
        """
        Do whatever is required of this type of request.
        
        Parameters
        ----------
        dbase : DataBase
            The file controller        
        
        Returns
        -------
        Varies by type, see source code.
        
        """
        if self.type == 'New File':
            (filepath, headers) = self.args
            dbase.startfile(filepath, headers)
            return None

        elif self.type == 'Open File':
            filepath = self.args
            headers = dbase.openfile(filepath)
            return headers

        elif self.type == 'Write Line':
            if dbase.file is not None:
                record = self.args
                dbase.writeline(record)
            return None

        elif self.type == 'Close File':
            dbase.closefile()
            return None

        elif self.type == 'Get Current File':
            return dbase.filepath, dbase.headers

        elif self.type == 'Read Unread':
            return dbase.readUnread()

        elif self.type == 'Read Latest':
            return dbase.latest

        elif self.type == 'Read All':
            hardlimit = 2000
            localtz = tzlocal.get_localzone()

            (xparam, yparams) = self.args
            if dbase.file is not None:
                dbase.clearUnread()
                xindex = dbase.headers.index(xparam)
                yindices = [dbase.headers.index(yparam) for yparam in yparams]
                xdata = [[] for yi in yindices]
                ydata = [[] for yi in yindices]
                try:
                    dbase.file.seek(0, 0)
                    dbase.file.readline()
                except ValueError:
                    dbase.openfile(dbase.filepath)
                    dbase.file.seek(0, 0)
                    dbase.file.readline()
                for line in dbase.file:
                    line = line.strip().split('\t')
                    for ii, yindex in enumerate(yindices):
                        if (line[xindex] != '-') and (line[yindex] != '-'):
                            if xparam == 'Timestamp':
                                timestamp = datetime.datetime.strptime(line[xindex], '%Y-%m-%d %H:%M:%S.%f')
                                timestamp = timestamp.replace(tzinfo=localtz)
                                xdata[ii].append(timestamp)
                            else:
                                xdata[ii].append(float(line[xindex]))
                            if yparams[ii] == 'Timestamp':
                                timestamp = datetime.datetime.strptime(line[xindex], '%Y-%m-%d %H:%M:%S.%f')
                                timestamp = timestamp.replace(tzinfo=localtz)
                                ydata[ii].append(timestamp)
                            else:
                                ydata[ii].append(float(line[yindex]))

                while len(xdata) > hardlimit:
                    xdata = [np.array(xd) for xd in xdata]
                    ydata = [np.array(yd) for yd in ydata]
                    if len(xdata) % 2 != 0:
                        xdata = [np.append(xd, xd[-1]) for xd in xdata]
                        ydata = [np.append(yd, yd[-1]) for yd in ydata]
                    xdata = [xd.reshape(int(len(xd)/2), 2) for xd in xdata]
                    xdata = [xd.transpose() for xd in xdata]
                    ydata = [yd.reshape(int(len(yd)/2), 2) for yd in ydata]
                    ydata = [yd.transpose() for yd in ydata]
                    xdata = [list(xd[0]) for xd in xdata]
                    ydata = [list(yd[0]) for yd in ydata]

                alldata = [(xdata[ii], ydata[ii]) for ii in range(len(xdata))]
                return alldata
            else:
                return [([],[])]
        else:
            print('Unknown file request!')


class DataBase:
    """
    Class for controlling and tracking data flow into and out of datafiles.
    No more than one file can be opened at a time.
    
    Parameters
    ----------
    logQ : multprocessing.Queue
        Queue for logging events
    
    Attributes
    ----------
    filepath : str
        path of the current file
    headers : list of str
        All of the column headers in the file
    file : file
        file handle for the data file itself
    unread : list of dict
        records appended to the file since the last time the GUI requested\
        more data: this local storage prevents needing to search the file\
        every time
    logger : logging.Logger
        object which pushes event logs to logQ
    """
    
    
    def __init__(self, logQ):
        self.filepath = None
        self.headers = None
        self.file = None
        self.unread = []
        self.latest = {}
                
        qh = logging.handlers.QueueHandler(logQ)
        self.logger = logging.getLogger('database')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(qh)


    def openfile(self, filepath):
        """
        Access an existing data file. If a file is currently open, this will close it\
        first before opening the new one.
        
        Parameters
        ----------
        filepath : str
            file to be opened
            
        Returns
        -------
        self.headers : list of str
            The names of the columns in this file.
        """
        self.unread = []
        if self.file is not None:
            self.file.close()
        self.filepath = filepath
        self.file = open(self.filepath, 'a+')
        self.file.seek(0, 0)
        self.headers = self.file.readline().strip().split('\t')
        self.logger.critical('opened an existing file: {:s}'.format(self.filepath))
        return self.headers


    def startfile(self, filepath, headers):
        """
        Create a new datafile and open it for access.
        
        Parameters
        ----------
        filepath : str
            The file to be opened
        headers : list of str
            The column headers 
        """
        self.unread = []
        self.closefile()
        self.filepath = filepath
        if self.file is not None:
            self.closefile()
        self.file = open(self.filepath, 'a+')
        self.headers = headers

        self.file.write('\t'.join(self.headers) + '\n')
        self.logger.critical('created a new file: {:s}'.format(self.filepath))

    def writeline(self, record):
        """
        Add a single data line to the file.
        
        Parameters
        ----------
        record : dict
            The headers and values to append to the file.\
            If record.keys() doesn't cover all of the headers for the \
            current file, then a dash ``'-'`` is written to the omitted\
            columns.
            
        """
        self.logger.critical('Actually writing to file')
        self.unread.append(record)
        for key in record.keys():
            self.latest[key] = record[key]
        dataline = ['-' for head in self.headers]
        for ii, head in enumerate(self.headers):
            if head in record.keys():
                dataline[ii] = str(record[head])
        dataline = '\t'.join(dataline)

        self.file.write(dataline + '\n')   # write the line to the file
        self.file.flush()  # push the changes to disk

    def closefile(self):
        """
        Terminate the connection to the file which is presently open.
        """
        self.unread = []
        if self.file is not None:
            self.file.close()
            self.logger.critical('closed a file'.format(self.filepath))
        self.file = None

    def readUnread(self):
        """
        Grab all of the records taken since the last read, then clears the\
        list of unread records.
        
        Returns
        -------
        unread : list of dict
            All unread records
        """
        localtz = tzlocal.get_localzone()
        unread = self.unread[:]
        N = len(unread)
        for ii in range(N):
            unread[ii]['Timestamp'] = datetime.datetime.strptime(unread[ii]['Timestamp'], '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=localtz)
        self.unread = []
        return unread

    def clearUnread(self):
        """
        Clears the unread record buffer.
        """
        self.unread = []
    