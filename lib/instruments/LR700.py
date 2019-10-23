import re
import time

from . import Parameter as pm
from . import InstClass


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class LR700(InstClass.Instrument):
    idnString = '\?SYNTAX'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 1
        self.visa.query_delay=0.01

        self.params.append(pm.Param('Autorange', w='AUTORANGE', t='disc', vals=[0,1], labels=['Off', 'On']))
        self.params.append(pm.Param('Excitation', w='EXCITATION', q='get6', t='disc', vals=range(7),
                                    labels=['20 uV', '60 uV', '200 uV', '600 uV', '2 mV', '6 mV', '20 mV'],
                                    qmacro=lambda: self.getStatus('E', 'Excitation')))

        self.params.append(pm.Param('Filter', w='FILTER', q='get6', t='disc', vals=[0,1,2], labels=['1 s', '3 s', '10 s'],
                                    qmacro=lambda: self.getStatus('F', 'Filter')))

        self.params.append(pm.Param('Resistance', q='GET 0', t='cont', units='Ohms', qmacro=lambda: self.getValue('0')))

        self.params.append(pm.Param('Mode', w='MODE', q='get6', t='disc', vals=[0,1], labels=['x1', 'x10'],
                                    qmacro=lambda: self.getStatus('M', 'Mode')))
        self.params.append(pm.Param('Offset', w='OFFSET=', t='disc', vals=['0', 'R'],
                                    labels=['Zero', 'Current Value']))
        self.params.append(pm.Param('Range', w='RANGE', q='get6', t='disc', vals=range(10),
                                    labels=['2 mOhms', '20 mOhms', '200 mOhms', '2 Ohms', '20 Ohms',
                                            '200 Ohms', '2 kOhms', '20 kOhms', '200 kOhms', '2 MOhms'],
                                            qmacro=lambda: self.getStatus('R', 'Range')))
        self.params.append(pm.Param('Select Sensor', w='SELECT S=', q='get6', t='disc', vals=['00','01','02','03'],
                                    labels=['0','1','2','3'], qmacro=lambda: self.getStatus('S', 'Select Sensor')))
        self.params.append(pm.Param('Variable Excitation Level', w='VAREXC =', q='get6', t='cont', units='%%',prec=0, pmax=99, pmin=5,
                                    qmacro=self.getVarExcite))
#        self.params.append(pm.Param('Variable Excitation Enabled', w='VAREXC ', t='disc', vals=[0,1],
#                                    labels=['Disabled', 'Enabled']))


        self.pnames = [p.name for p in self.params]

    def getVarExcite(self, *args):
        ii=0
        while ii<5:
            try:
                response = self.visa.query('GET 6')
                pattern = '([^,]+)\%'
                answer = re.search(pattern, response).group(1)
                return [answer]
            except TypeError:
                ii+=1

    def getValue(self, channel, *args):
        ii=0
        while ii<5:
            try:
                response = self.visa.query('GET ' + channel+'\n')
                parse = re.search('([\+\-]\d+\.\d+) (.+)OHM (.+)', response)
                val = float(parse.group(1))
                mult_LUT = {'K':1e3, ' ':1, 'M':1e-3, 'U':1e-6}
                return [str(val*mult_LUT[parse.group(2)])]
            except AttributeError:
                ii+=1

    def getStatus(self, channel, param, *args):
        ii=0
        while ii<5:
            try:
                response = self.visa.query('GET 6')
                pattern = '([^,]+)'+channel
                answer = int(re.search(pattern, response).group(1))
                thisparam = self.getParam(param)
                answer = thisparam.labels[answer]
                return [answer]
            except AttributeError:
                ii+=1
