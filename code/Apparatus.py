import pyvisa
import re
import instruments as li
import commands as sc
import HelperFunctions as hf
import logging

class Apparatus:
    """ An Apparatus object describes the entire target experiment, which \
    includes:
    
    * Instrument configuration and communication
    * Sequence writing and execution
    
    Attributes
    ----------
    addrsList : list of str
        The GPIB addresses which are currently detected by the drivers
    instList : list of instruments.InstClass.Instrument
        All of the instruments accessible to the apparatus, including \
        those which have not been
    rm : pyvisa.ResourceManager
        The object which handles communication between instruments
    sequence : list of SeqCommand
        The sequence to be run during the measurement
    exp : ExpGUI
        Link to the GUI
    logger : logging.Logger
        handles generation of log files for error reporting and metadata
    
    Parameters
    ----------
    exp : ExpGUI
        Experiment controller object creating the apparatus.
    """
    
    def __init__(self, exp):
        self.addrsList = []
        self.instList = []
        self.rm = pyvisa.ResourceManager()
        self.sequence = []
        self.exp = exp
        
        logging.basicConfig(filename=exp.getLogPath(), level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.logger.info('Created an apparatus object')

    
    def serialize(self):
        """ Create a simplified, compressed description of the Apparatus.
        
        When the user presses the "RUN" button, we spawn new processes to \
        handle all of the instrument communications separate from slow \
        things like plotting and updating the GUI.  This creates a copy of \
        the apparatus settings and sequence commands which can be passed \
        to the child process.
        
        Returns
        -------
        serial : str
            A single, human-readable string describing the Apparatus state.
            It's split into sections for instruments and commands.
        """
        serial = 'INSTRUMENTS:\n'
        # Get instruments:
        for inst in self.instList:
            if inst.name is not None:
                serial += '{:s}\t{:s}\t{:s}\n'.format(inst.address, inst.model, str(inst.name))
            else:
                serial += '{:s}\t{:s}\n'.format(inst.address, inst.model)

        # Get sequence commands
        serial += 'COMMANDS:\n'
        for cmd in self.sequence:
            serial += cmd.description()
        return serial
    
    
    def deserialize(self, serialapp, gui=None):
        """ 
        Take a serialized string object description of the apparatus as \ 
        defined on the GUI, and rebuild it.  This is intended to run once\
        at the beginning of each experiment.
        
        Parameters
        ----------
        serialapp : str
            String serialization of an apparatus, produced by serialize()
        gui : ExpGUI, optional
            Link to a gui object to be used in rebuilding the apparatus. \
            If the serialization is being used for logging, gui is not \
            required.  Defaults to None.

        """
        self.instList = []
        lines = serialapp.split('\n')
        stop = lines.index('COMMANDS:')
        for line in lines[1:stop]:
            try:
                iaddr, imodel, iname = line.strip().split('\t')
            except ValueError:
                iaddr, imodel = line.strip().split('\t')
                iname = None
            
            modelType = None  # start ignorant
            for model in li.InstClass.Instrument.__subclasses__():  # compare to all known models
                if imodel == model.__name__:  # if the IDN response matches the model's string,
                    modelType = model  # we have what we came for
                    break  # get in the car
                if modelType is not None:
                    break
            if modelType is not None:  # we got a match, now make it so
                self.instList.append(modelType(self, iaddr, name=iname))
        cmdpos = []
        for ii, line in enumerate(lines):
            if re.match('Sequence Command', line):
                cmdpos.append(ii)

        # parse the sequence into a list of dicts, one for each step
        line = ''
        index = stop+1
        allSteps = []

        while index<len(lines):
            line = lines[index]
            index += 1
            if line != '':
                if re.match('Sequence Command', line) is not None:
                   allSteps.append({})
                elif line[0] == '\t':
                   try:
                       name = re.search('(.+) =', line.strip()).group(1)
                       try:
                           val = re.search('= (.+)', line.strip()).group(1)
                       except AttributeError:
                           val = ''
                       if val != '':
                           if val[0] == '[':
                               val = val.split(',')
                               val = [x.strip('[]"\' ') for x in val]
                           if name == 'rows':
                               allSteps[-1][name] = int(val)
                           elif name == 'enabled':
                               allSteps[-1][name] = (val.strip()=='True')
                           else:
                               try:
                                   allSteps[-1][name] = float(val)
                               except (ValueError, TypeError):
                                   allSteps[-1][name] = val
                   except AttributeError:
                       pass

        looplist = []
        for step in allSteps:
            typedict = {'SetCommand':sc.SetCmd, 'WaitCommand':sc.WaitCmd, 'SingleMeasurementCommand':sc.SMeasCmd,
                        'ContinuousMeasurementCommand':sc.CMeasCmd, 'LoopCommand':sc.LoopCmd,
                        'LoopEndCommand':sc.LoopEnd}
            newstep = typedict[step['type']](self.exp, self, len(self.sequence), dup=True, gui=gui)
            if isinstance(newstep, sc.LoopCommand.LoopCmd):
                looplist.append(newstep)
            if isinstance(newstep, sc.LoopEnd):
                newstep.loop = looplist[-1]
                del looplist[-1]
                newstep.loopPos = self.sequence.index(newstep.loop)

            for key in step.keys():
                newstep.__dict__[key] = step[key]
            
            newstep.updateInstList()
            self.sequence.append(newstep)


    def findInstruments(self):
        """
        Makes current the lists of instruments by doing the following:
        
        * Query all instruments on VISA for IDN strings
        * if it detects a newly attached instrument, it adds it to the list
        * if it notices an address is now missing, it removes it from lists
        * if an address has changed instrument type, it removes it from \
        the active lists and add it to available.
        
        Otherwise, instruments are left as they are.
        
        No parameters, no returns.
        """

        self.addrsList = list(self.rm.list_resources())  # Determine what addresses are available
        currentInsts = {x.address:x for x in self.instList}
        self.instrNames = {x.address:x.name for x in self.instList}
        self.instList = []

        # Rebuild the list of available instruments from scratch
        for addr in self.addrsList:  # for each one....
            if re.match('ASRL', addr) is None:
                try:
                    resource = self.rm.open_resource(addr)  # open a VISA session
                    addrnum = int(re.search('::(.+)::', addr).group(1))
                    if addrnum <= 20:
                        idn = resource.query('*IDN?')  # ask it what's good
                    else:
                        idn = resource.query('ID')
                        
                except pyvisa.errors.VisaIOError:  # if an address throws a fit
                    self.addrsList.remove(addr)  # cut that address so nobody else tries

                modelType = None  # start ignorant
                for model in li.InstClass.Instrument.__subclasses__():  # compare to all known models
                    if re.match(model.idnString, idn):  # if the IDN response matches the model's string,
                        modelType = model  # we have what we came for
                        break  # get in the car
                    if modelType is not None:
                        break

                if modelType is not None:  # we got a match, now make it so
                    self.instList.append(modelType(self, addr))  # create the instrument and add it to the list
                    
        # Compare new list to the active and available lists of the exp, refresh
        for instr in self.instList:
            if instr.address in currentInsts.keys():
                if instr.model == currentInsts[instr.address].model:
                    if currentInsts[instr.address].name is not None:
                        instr.name = currentInsts[instr.address].name


    def get_availInsts(self):
        """ Returns list of instruments currently accessible
        
        Returns
        -------
        availInsts : list of instruments.InstClass.Instrument
            instrument objects currently actives
        """
        availInsts = []
        for inst in self.instList:
            if inst.name is None:
                availInsts.append(inst)
        return availInsts


    def get_activeInsts(self):
        """Get the instrument objects which are currently activated.
        
        Returns
        -------
        activeInsts : list of instruments.InstClass.Instrument
            List of instrument objects currently active
            
        """
        activeInsts = []
        for inst in self.instList:
            if inst.name is not None:
                activeInsts.append(inst)
        return activeInsts


    def getVarsList(self):
        """ Get list of variables generated by the current sequence
        
        Returns
        -------
        varslist : list of str
            list of variable names
        """
        varslist = ['Timestamp']
        for step in self.sequence:
            if step.enabled:
                steplist = step.getMeasHeaders()
                for var in steplist:
                    if var not in varslist:
                        varslist.append(var)
        return varslist


    def disconnectInstr(self, instr):
        """
        Purge all lists of references to the given instrument.
        
        Parameters
        ----------
        instr : Instrument
            Object to be removed.
        """
        if instr in self.instList:
            self.instList.remove(instr)


    def updateInsts(self, insts):
        """ Apply the changes made in the apparatus lists to the instrument\
        objects themselves.  This currently applies only to names.
        
        Parameters
        ----------
        insts : list of instruments.InstClass.Instrument
            the instrument objects to be updated
        """
        self.instList = insts
        for instref in self.instList:
            inst = next(x for x in self.instList if x.address==instref.address)
            if instref in self.get_activeInsts():
                inst.setName(instref.name)
            else:
                inst.clearName()

    
    
    # SEQUENCE STUFF

    def updateTitles(self):
        """
        Bring the sequence command titles (the text seen by the user in \
        the sequence listing) up to date with the contents of the commands.
        
        No parameters, no returns.
        """
        for step in self.sequence:
            pos = self.sequence.index(step)
            step.pos = pos
            step.updateTitle()
            loopdepth = 0
            for priorCmd in self.sequence[:pos]:
                if isinstance(priorCmd, sc.LoopCmd):
                    loopdepth += 1
                elif isinstance(priorCmd, sc.LoopEnd):
                    loopdepth -= 1
            if isinstance(step, sc.LoopEnd):
                loopdepth -= 1

            step.title = hf.indentLoops(step, loopdepth)


    def runSequence(self, fileReqQ):
        """  Execute the given sequence.  This function reads the sequence\
        and executes each command, conditioned on abort or disable flags.\
        As each step is reached, it keeps track of the present position
        within the sequence.
        
        All of the details of the execution, including the steps themselves\
        but also the GUI display, is stored within other objects.
        
        Parameters
        ----------
        fileReqQ : Queue
            The queue to enable communication to and from the file read/\
            write processes running in parallel.  This is passed through to
            the `command.execute()` function.
        """
        position = 0
        seqLength = len(self.sequence)
        while not self.exp.isAborted():
            while position < seqLength:
                cmd = self.sequence[position]
                if cmd.enabled:
                    if isinstance(cmd, sc.LoopEnd):
                        self.exp.instAns = cmd.status
                        newPosition = cmd.execute(fileReqQ)
                        position = newPosition if (newPosition is not None) else (position + 1)
                    else:
                        self.exp.instAns = cmd.status
                        cmd.execute(fileReqQ)
                        position += 1
                else:
                    position += 1
            self.exp.abort()

        self.exp.finish()

        print('done!')


    def deleteSteps(self, indices):
        """ Cut sequence commands from the list.
        
        This first runs through and finds if any of the selected indices\
        are either half of a loop command, and if so, it adds the index of\
        the other half if it has not already been selected.
        
        Parameters
        ----------
        indices : list of int
            command step indices to be deleted
        """
        for ii in indices:
            if isinstance(self.sequence[ii], sc.LoopCmd):
                for jj, cmd in enumerate(self.sequence):
                    if isinstance(cmd, sc.LoopEnd):
                        if cmd.loop == self.sequence[ii]:
                            if jj not in indices:
                                indices.append(jj)
                                indices = sorted(indices)
                            break
            if isinstance(self.sequence[ii], sc.LoopEnd):
                parentLoopIndex = self.sequence.index(self.sequence[ii].loop)
                if parentLoopIndex not in indices:
                    indices.append(parentLoopIndex)
                    indices = sorted(indices)
        for ii in indices[::-1]:
            del self.sequence[ii]


    def protectLoops(self):
        """ Swap positions of commands such that the heirarchy always\
        makes sense.
        
        No parameters, no returns.
        """
        # check to make sure loops aren't screwed up by the move
        for ii, cmd in enumerate(self.sequence):  # if an end is before its loop, flip the two.
            if isinstance(cmd, sc.LoopEnd):
                jj = self.sequence.index(cmd.loop)
                if ii<jj:
                    del self.sequence[ii]
                    self.sequence.insert(ii, cmd.loop)
                    del self.sequence[jj]
                    self.sequence.insert(jj, cmd)

        activeloops = []
        for ii, cmd in enumerate(self.sequence):  # if a loop is nested, make sure its end is nested in the same way
            if isinstance(cmd, sc.LoopCmd):
                activeloops.append(cmd)
            elif isinstance(cmd, sc.LoopEnd):
                if cmd.loop is not activeloops[-1]:  # there's a nesting error
                    for jj in range(ii,len(self.sequence)):  # search through the rest of the sequence
                        if isinstance(self.sequence[jj], sc.LoopEnd): # for the other loop ends
                            if self.sequence[jj].loop is activeloops[-1]:  # find the one which ends the active loop
                                end = self.sequence[jj]
                                del self.sequence[jj] # and move it up
                                self.sequence.insert(ii,end)
    
    
    def getSequence(self):
        """ Getter function for the sequence itself
        
        Returns
        -------
        list of str
            the string descriptions of all steps.
        """
        return [str(x) for x in self.sequence]


    def getSeqEnabled(self):
        """ Getter function for enabled flags of each cmd in the sequence
        
        Returns
        -------
        list of bool
            `True` indicates that the cmd will run.
        """
        return [x.enabled for x in self.sequence]


    def appendSequence(self, step, pos):
        """ Add a new step into the sequence
        
        Parameters
        ----------
        step : SeqCommand
            the step to be inserted
        pos : int
            Position *above which* to insert the new step.
        """
        
        self.sequence.insert(pos, step)