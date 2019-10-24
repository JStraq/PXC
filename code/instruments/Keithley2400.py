from . import Parameter as pm
from . import InstClass

# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Keithley2400(InstClass.Instrument):
    idnString = 'KEITHLEY INSTRUMENTS INC.,MODEL 2400'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        
        #self.params.append(pm.Param('Output State', q='OUTP:STAT?', w='OUTP:STAT', t='disc', vals=[0,1], labels=['Off', 'On']))
        #self.params.append(pm.Param('Enabled Functions', q='SENS:FUNC:ON?', t='cont', units=''))
        #self.params.append(pm.Param('Get Data', q='SENS:DATA:LAT?', t='cont', units=''))
#        self.params.append(pm.Param('Resistance', q='measres', t='cont', units='', qmacro=self.getResistance))
        self.params.append(pm.Param('VIR', q='iv', t='cont', qmacro=self.getVIR, comps=['Voltage', 'Current', 'Resistance'],
                                    units=['V','A','Ohms']))
        #self.params.append(pm.Param('Latest Data', q='SENS:DATA:LAT?', t='cont', units=''))
        #self.params.append(pm.Param('Read', q='READ?', t='cont', units=''))
        #self.params.append(pm.Param('Resistance', q='MEAS:RES?', t='cont', units='Ohms',qmacro=self.getResistance))


        self.pnames = [p.name for p in self.params]
        
    def getResistance(self):
        response = self.visa.query('MEAS:RES?')
        res = response.split(',')[2]
        return [res]
    
    def getVIR(self):
        response = self.visa.query('MEAS?')
        v,i = response.split(',')[:2]
        r = str(float(v)/float(i))
        return [v, i, r]