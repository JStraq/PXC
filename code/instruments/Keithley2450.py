from . import Parameter as pm
from . import InstClass

class Keithley2450(InstClass.Instrument):
    idnString = 'KEITHLEY INSTRUMENTS INC.,MODEL 2450'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        
        self.params.append(pm.Param('OutputState', q='OUTP:STAT?', w='OUTP:STAT', t='disc', vals=[0,1], labels=['Off', 'On']))
        self.params.append(pm.Param('OutputVoltage', q='SOUR:VOLT?', w='SOUR:VOLT ', t='cont', pmin=-210, pmax=210, units='V'))

        self.pnames = [p.name for p in self.params]        