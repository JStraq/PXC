import abc
import time
import pyvisa

class InstRef():
    def __init__(self, inst):
        self.address = inst.address
        self.name = inst.name
        self.model = inst.model
    def __str__(self):
        if self.name is not None:
            return '{:s}:{:s}:{:s}'.format(self.name, self.address[7:9].strip(':'), self.model)
        else:
            # return '{:s} -- {:s}'.format(self.address, self.model)
            return '{:s}:{:s}'.format(self.address[7:9].strip(':'), self.model)

    def __repr__(self):
        return self.__str__()
        
    def setName(self, name):
        self.name = name
    def clearName(self):
        self.name = None

class Instrument(metaclass=abc.ABCMeta):
    """
    Abstract class describing a generalized instrument.
    """

    # Initialize instrument name and address.

    def __init__(self, apparatus, address, name=None):
        self.apparatus = apparatus
        self.address = address
        self.name = name
        self.params = []
        self.pnames = None
        self.model = type(self).__name__
        self.visa = self.apparatus.rm.open_resource(self.address)
        self.writeDelay = 0

    def __str__(self):
        if self.name is not None:
            return '{:s}:{:s}:{:s}'.format(self.name, self.address[7:9].strip(':'), self.model)
        else:
            # return '{:s} -- {:s}'.format(self.address, self.model)
            return '{:s}:{:s}'.format(self.address[7:9].strip(':'), self.model)

    def __repr__(self):
        return self.__str__()

    def getAddress(self):
        """
        Return instrument address (GPIB::NUMBER::INSTR)
        """
        return self.address

    def getName(self):
        """
        Returns the instrument name
        """
        return self.name

    def setName(self, name):
        # protect name format?
        self.name = name

    def clearName(self):
        self.name = None

    def getSeqCommands(self):
        return self.seqCommands

    def getWParams(self):
        """
        Returns a list of all writable parameters
        """
        wparams = []
        for pm in self.params:
            if pm.write is not None:
                wparams.append(pm)
        return wparams

    def getWCParams(self):
        """
        Returns a list of all writable continuous parameters
        """
        wparams = []
        for pm in self.params:
            if pm.write is not None:
                if pm.type != 'cont':
                    wparams.append(pm)
        return wparams

    def getWCSParams(self):
        """
        Returns a list of all writable, continuous, simple parameters
        """
        wparams = []
        for pm in self.params:
            if pm.write is not None and pm.type == 'cont' and pm.comps is None:
                wparams.append(pm)
        return wparams

    def getQParams(self):
        """
        Returns a list of all queryable parameters
        """
        qparams = []
        for pm in self.params:
            if pm.query is not None:
                qparams.append(pm)
        return qparams

    def getQCParams(self):
        """
        Returns a list of all readable continuous parameters
        """
        qparams = []
        for pm in self.params:
            if pm.query is not None and pm.type == 'cont':
                qparams.append(pm)
        return qparams

    def getQCSParams(self):
        """
        Returns a list of all readable, continuous, simple parameters
        """
        qparams = []
        for pm in self.params:
            if pm.query is not None and pm.type == 'cont' and pm.comps is None:
                qparams.append(pm)
        return qparams

    def getParam(self, param):
        try:
            thisparam = self.params[self.pnames.index(param)]
            return thisparam
        except ValueError:
            iscomp = False
            for pm in self.params:
                try:
                    if param in pm.comps:
                        iscomp=True
                        break
                except TypeError:
                    pass
            if iscomp:
                return pm
            else:
                raise ValueError('No such parameter!')

    def readParam(self, param):
        try:
            thisparam = self.params[self.pnames.index(param)]
            if thisparam.query is None:
                print("'{:s}' is a write-only parameter!".format(param))
        except ValueError:
            print("No parameter with that name exists!  Options are:")
            print(self.pnames)
            return None

        if thisparam.qmacro is None:
            attempts = 0
            limit = 10
            while attempts < limit:
                try:
                    if attempts > 0:
                        self.visa.clear()
                    print(thisparam.query, end='  --  ')
                    out = self.visa.query(thisparam.query).strip()
                    if thisparam.type == 'disc':
                        out = '{:s},{:s}'.format(out, thisparam.labels[thisparam.vals.index(str(int(out)))])  # forces '00' to match '0'
                        print(out)
                        return [out]
                    else:
                        print(out)
                        out = out.split(',')
                        for ii,val in enumerate(out):
                            try:
                                val = str(float(val))  # this strips leading zeros from float strings
                                out[ii] = val
                            except ValueError:
                                pass
                        return out

                except KeyError:
                    print("The {:s} at address {:s} doesn't have a parameter named '{:s}'".format(self.model, self.address,
                                                                                                  param))
                    return None
                except ValueError:
                    if attempts < limit:
                        print("Received unexpected value for discrete parameter, retrying:")
                        out = (out, 'Unknown')
                        print(out)
                        attempts += 1
                    else:
                        return "Received strange data too many times!:" + out
                except pyvisa.errors.VisaIOError:
                    if attempts < limit:
                        print('Command timout, retrying...')
                        attempts += 1
                    else:
                        return 'Command timed out too many times:' + thisparam.query

        else:  # MACRO COMMANDS
            thisparam = self.params[self.pnames.index(param)]
            return thisparam.qmacro()

    def writeParam(self, param, val=None):
        try:
            thisparam = self.params[self.pnames.index(param)]
            if thisparam.write is None:
                print("'{:s}' is a read-only parameter!".format(param))
                return None
        except ValueError:
            print("No parameter with that name exists!  Options are:")
            print(self.pnames)
            return None

        if thisparam.wmacro is None:
            try:
                if not isinstance(val, list):
                    val = [val]

                if thisparam.type == 'cont':
                    fmtstring = ['{:f}' for x in range(len(val))]
                    for ii in range(len(val)):
                        try:
                            val[ii] = float(val[ii])
                            if thisparam.prec is not None:
                                val[ii] = round(val[ii], thisparam.prec)
                                fmtstring[ii] = '{{:.{:d}f}}'.format(thisparam.prec)
                            if thisparam.pmax is not None:  # Truncate the parameter to the closest limit if out of range
                                val[ii] = min(val[ii], thisparam.pmax)
                            if thisparam.pmin is not None:
                                val[ii] = max(val[ii], thisparam.pmin)
                        except TypeError:
                            print('Invalid Parameter!')
                elif thisparam.type == 'disc':
                    fmtstring = ['{:d}' for x in range(len(val))]
                    for ii in range(len(val)):
                        val[ii] = str(val[ii])
                        if val[ii] not in thisparam.vals:
                            if val[ii] not in thisparam.labels:
                                raise ValueError
                            else:  # the user input the label instead of the value...alright fiiiiine
                                val[ii] = thisparam.vals[thisparam.labels.index(val[ii])]
                cmd = '{:s}'.format(thisparam.write)
                if thisparam.type != 'act':
                    for ii in range(len(val)):  # for multiple inputs, use syntax 'command a,b,c'
                        delim = ' ' if ii == 0 else ','
                        if thisparam.type == 'cont':
                            cmd = ('{:s}{:s}' + fmtstring[ii]).format(cmd, delim, float(val[ii]))
                        elif thisparam.type == 'disc':
                            cmd = ('{:s}{:s}' + fmtstring[ii]).format(cmd, delim, int(val[ii]))
                print(cmd)
                self.visa.write(cmd)
                time.sleep(self.writeDelay)

            except ValueError:
                print("The parameter '{:s}' can't accept value '{:s}'.  Acceptable values are:".format(param, str(val)))
                try:
                    for ii, val in enumerate(thisparam.vals):
                        if thisparam.labels is not None:
                            print('{:s}\t{:s}'.format(val, thisparam.labels[ii]))
                        else:
                            print(val)
                except TypeError:
                    if thisparam.pmax is not None:
                        if thisparam.pmin is not None:
                            print('{:f} < val < {:f}'.format(thisparam.pmin, thisparam.pmax))
                        else:
                            print('val < {:f}'.format(thisparam.pmax))
                    else:
                        if thisparam.pmin is not None:
                            print('{:f} < val'.format(thisparam.pin))
                        else:
                            print('Literally anything. Sorry, Mario, but your error is in another castle.')

        else:  # MACRO COMMANDS
            thisparam = self.params[self.pnames.index(param)]
            thisparam.wmacro(val)
            time.sleep(self.writeDelay)

    def clearGPIB(self):
        self.visa.write('*CLS')
        print('*CLS')

    
    def configInst(self):
        qps = self.getQParams()
        wps = self.getWParams()
            