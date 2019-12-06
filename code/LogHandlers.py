import logging
import logging.config
import logging.handlers

class PXCLogger(logging.handlers.QueueListener):
    def __init__(self, logQ, handlers):
        print(handlers)
        
#        if not os.path.exists(r'C:/Data/PXCLogs'):
#            os.makedirs(r'C:/Data/PXCLogs')
#        self.logpath = 'C:/Data/PXCLogs/PxcSession_{:s}.log'.format(dt.strftime(dt.now(),'%Y-%m-%d_%H-%M-%S'))
        logging.handlers.QueueListener.__init__(self, logQ, handlers)
        print(self.handlers)
        self.filehand = self.handlers[0][0]
        self.conhand = self.handlers[0][1]
        self.recfmt = logging.Formatter('%(asctime)s\t %(name)-8s %(levelname)-8s %(processName)-8s %(message)s')
        self.metafmt = logging.Formatter('#####\t\t%(message)s')
        
        self.filehand.setFormatter(self.recfmt)
       

    def handle(self, record):
        if record.name == 'meta':
            self.filehand.setFormatter(self.metafmt)
            self.filehand.handle(record)
            self.filehand.setFormatter(self.recfmt)
        else:
            self.filehand.handle(record)
        
        
#        self.conhand.setFormatter(self.fmts[record.name])
        self.conhand.handle(record)