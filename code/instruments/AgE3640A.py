from . import InstClass
from .import Parameter as pm


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class AgE3640A(InstClass.Instrument):
    idnString = 'Agilent Technologies,E3640A'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 0.01

        self.params.append(pm.Param('Voltage', q='VOLT?', w='VOLT', t='cont', units='V'))
        self.params.append(pm.Param('Current', q='CURR?', w='CURR', t='cont', units='A'))

        self.pnames = [p.name for p in self.params]