import Apparatus as ap
import logging

def instHandler(*args):
    """
    Autonomous code which handles the execution of the sequence steps.
    This code will run in its own process and ship data around through
    the fileReqQ.  It is never intended to receive instructions, and runs
    without woryying about the GUI or the file.
    """
    exp, instReqQ, fileReqQ, logQ, appcopy = args
    
    qh = logging.handlers.QueueHandler(logQ)
    logger = logging.getLogger('inst')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(qh)
    
    logger.info('Starting Instrument Process')
    
    print('inst_init')
    try:
        app = ap.Apparatus(exp, logQ)
        app.deserialize(appcopy)
        app.runSequence(fileReqQ)
        exp.endSeq()
    except Exception as e:
        logger.info('Unhandled exception occured in instHandlers:')        
        logger.exception(e)

    print('kill_insts')
    app.rm.close()
    return None
