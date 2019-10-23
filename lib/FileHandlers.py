from datetime import datetime
import numpy as np
import logging


def fileHandler(args):
    print('init_files')
    exp, fileReqQ= args
    
    logging.basicConfig(filename=exp.getLogPath()+'f', level=logging.INFO)
    log = logging.getLogger(__name__)
    log.info('Start File Process')
    
    database = dataBase()
    
    while not exp.get_killFlag():
        if not fileReqQ.empty():
            try:
                req = fileReqQ.get()
            except EOFError as e:
                log.info('FileReqQ has crashed')
                log.exception(e)
            try:
                if req.type == 'Read Latest':
                    exp.set_fileLatest(req.execute(database))
                else:
                    exp.set_fileAns(req.execute(database))
            except Exception as e:
                log.info('Unhandled exception happened in file process')
                log.info('while processing {:s}-type fileRequest'.format(req.type))
                log.exception(e)
            fileReqQ.task_done()

    if database is not None:
        database.closefile()  # don't do drugs, close your files, stay in school
    print('kill_files')



class fileRequest:
    def __init__(self, reqtype, args=None):
        self.type = reqtype
        self.args = args

    def execute(self, database):
        if self.type == 'New File':
            (filepath, headers) = self.args
            database.startfile(filepath, headers)
            return None

        elif self.type == 'Open File':
            filepath = self.args
            headers = database.openfile(filepath)
            return headers

        elif self.type == 'Write Line':
            if database.file is not None:
                record = self.args
                database.writeline(record)
            return None

        elif self.type == 'Close File':
            database.closefile()
            return None

        elif self.type == 'Get Current File':
            return database.filepath, database.headers

        elif self.type == 'Read Unread':
            return database.readUnread()

        elif self.type == 'Read Latest':
            return database.latest

        elif self.type == 'Read All':
            hardlimit = 2000

            (xparam, yparams) = self.args
            if database.file is not None:
                database.clearUnread()
                xindex = database.headers.index(xparam)
                yindices = [database.headers.index(yparam) for yparam in yparams]
                xdata = [[] for yi in yindices]
                ydata = [[] for yi in yindices]
                try:
                    database.file.seek(0, 0)
                    database.file.readline()
                except ValueError:
                    database.openfile(database.filepath)
                    database.file.seek(0, 0)
                    database.file.readline()
                for line in database.file:
                    line = line.strip().split('\t')
                    for ii, yindex in enumerate(yindices):
                        if line[xindex] is not '-' and line[yindex] is not '-':
                            if xparam == 'Timestamp':
                                xdata[ii].append(datetime.strptime(line[xindex], '%Y-%m-%d %H:%M:%S.%f'))
                            else:
                                xdata[ii].append(float(line[xindex]))
                            if yparams[ii] == 'Timestamp':
                                ydata[ii].append(datetime.strptime(line[yindex], '%Y-%m-%d %H:%M:%S.%f'))
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


class dataBase:
    def __init__(self):
        self.filepath = None
        self.headers = None
        self.file = None
        self.unread = []
        self.latest = {}

    def openfile(self, filepath):
        self.unread = []
        if self.file is not None:
            self.file.close()
        self.filepath = filepath
        self.file = open(self.filepath, 'a+')
        self.file.seek(0, 0)
        self.headers = self.file.readline().strip().split('\t')
        return self.headers

    def startfile(self, filepath, headers):
        self.unread = []
        self.closefile()
        self.filepath = filepath
        if self.file is not None:
            self.closefile()
        self.file = open(self.filepath, 'a+')
        self.headers = headers

        self.file.write('\t'.join(self.headers) + '\n')

    def writeline(self, record):
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
        self.unread = []
        if self.file is not None:
            self.file.close()
        self.file = None

    def readUnread(self):
        unread = self.unread[:]
        self.unread = []
        return unread

    def clearUnread(self):
        self.unread = []