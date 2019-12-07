import logging
import logging.handlers

class PXCLogger(logging.handlers.QueueListener):
    """
    Specialized subclass of the standard ``logging.handlers.QueueListener``\
    class.  A ``PXCLogger`` instance will wait for log records to enter\
    the queue, then format them properly depending on where they came from.
    
    Parameters
    ----------
    logQ : multiprocessing.Queue
        The queue which this object will monitor
    handlers : list of logging.Handler
        List of the various types of handlers.  Currently this supports\
        only two handlers, one to the file and one to the console.
    """
    def __init__(self, logQ, handlers):        
        logging.handlers.QueueListener.__init__(self, logQ, handlers)
        self.filehand = self.handlers[0][0]
        self.conhand = self.handlers[0][1]
        self.recfmt = logging.Formatter('%(asctime)s\t %(name)-8s %(levelname)-8s %(processName)-8s %(message)s')
        self.metafmt = logging.Formatter('#####\t\t%(message)s')
        
        self.filehand.setFormatter(self.recfmt)
       

    def handle(self, record):
        """
        Select a formatter and pass the record to the file and console\
        handlers.
        
        Parameters
        ----------
        record : logging.LogRecord
            The record to be logged.  This currently uses a standard format\
            for all logger sources except for the one called ``'meta'``,\
            which uses a simpler format which looks more like a tag.
        """
        if record.name == 'meta':
            self.filehand.setFormatter(self.metafmt)
            self.filehand.handle(record)
            self.filehand.setFormatter(self.recfmt)
        else:
            self.filehand.handle(record)
        self.conhand.handle(record)