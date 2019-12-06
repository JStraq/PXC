import Apparatus as ap
import logging

def instHandler(*args):
    exp, instReqQ, fileReqQ, logQ, appcopy = args
    
    qh = logging.handlers.QueueHandler(logQ)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)
    

    logger.info('Starting Instrument Process--------------------------------------------------------')
    
    print('inst_init')
    try:
        app = ap.Apparatus(exp)
        app.deserialize(appcopy)
        app.runSequence(fileReqQ)
        exp.endSeq()
    except Exception as e:
        logger.info('Unhandled exception occured in instHandlers:')        
        logger.exception(e)

    print('kill_insts')
    return None
   


class instRequest:
    def __init__(self, reqtype, args=None):
        self.type = reqtype
        self.args = args

    def execute(self, app):
        if self.type == 'Read Monitors':
            monInsts, monParams = self.args
            insts = monInsts[:]
            params = monParams[:]
            compIndices = [0for x in monInsts]
            vals = []
            stringInsts = [str(x) for x in app.activeInstList]
            for ii in range(len(monInsts)):
                try:
                    insts[ii]= app.activeInstList[stringInsts.index(monInsts[ii])]    # convert to actual objects
                except ValueError:
                    insts[ii] = None
                if insts[ii] is not None:
                    try:
                        params[ii] = insts[ii].getParam(monParams[ii])
                        if params[ii].comps is not None:
                            compIndices[ii] = params[ii].comps.index(monParams[ii])
                    except ValueError:
                        params[ii] = None
            
            for ii in range(len(insts)):
                if insts[ii] is not None and params[ii] is not None:
                    vals.append(insts[ii].readParam(str(params[ii]))[compIndices[ii]])
                else:
                    vals.append(None)
            return vals
        else:
            print('App request of unknown type!')
