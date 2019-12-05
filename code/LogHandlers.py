import logging as lg
import threading as th

class LogHandler(lg.Handler):
    
    def __init__(self, filename, logQ):
        lg.Handler.__init__(self)
        self.logger = lg.getLogger('pxc_log')
        self.filename = filename
        self.handler = lg.FileHandler(filename)
        self.q = logQ
        
        thread = th.Thread(target = self.listen)
        thread.daemon = True
        thread.start()
        
    def listen(self):
        while True:
            try:
                rec = self.q.get()
                self.handler.emit(rec)
            except EOFError:
                break
            except:
                raise
    
    def emit(self, record):
        with open(self.filename, 'a+') as logfile:
            logfile.write(record.msg)
            
    def send(self, record):
        self.q.put_nowait(record)