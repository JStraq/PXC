from . import Parameter as pm
from . import InstClass

# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Keithley6517B(InstClass.Instrument):
    idnString = 'KEITHLEY INSTRUMENTS INC.,MODEL 6517B'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        
        self.params.append(pm.Param('Voltage', q='MEAS:VOLT?', t='cont', qmacro=self.parseVolts))

        self.pnames = [p.name for p in self.params]
        
    def parseVolts(self):
        response = self.visa.query('MEAS:VOLT?')
        return [response.split('NVDC')[0]]