from . import InstClass
from . import Parameter as pm

# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Keithley6221(InstClass.Instrument):
    idnString = 'KEITHLEY INSTRUMENTS INC.,MODEL 6221'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        
        self.params.append(pm.Param('AbortWave', w='SOUR:WAVE:ABOR', t='act'))
        self.params.append(pm.Param('ArmWave', w='SOUR:WAVE:ARM', t='act'))
        self.params.append(pm.Param('InitWave', w='SOUR:WAVE:INIT', t='act'))
        self.params.append(pm.Param('PhaseMarkerStatus', w='SOUR:WAVE:PMAR:STAT', q='SOUR:WAVE:PMAR:STAT',t='disc',vals=[0,1],labels=['Off','On']))
        self.params.append(pm.Param('WaveAmplitude', w='SOUR:WAVE:AMPL', q='SOUR:WAVE:AMPL?', t='cont', pmax=105e-3, pmin=0, units='A'))
        self.params.append(pm.Param('Frequency', w='SOUR:WAVE:FREQ', q='SOUR:WAVE:FREQ?', t='cont', pmin=1e-3, pmax=1e5,units='Hz'))
        self.params.append(pm.Param('Offset', w='SOUR:WAVE:OFFS', q='SOUR:WAVE:OFFS?', t='cont', pmin=-105e-3, pmax=105e-3, units='A'))
        self.params.append(pm.Param('Compliance', w='SOUR:CURR:COMP', q='SOUR:CURR:COMP?', t='cont', pmax=105, pmin=0.1, units='V'))
        self.params.append(pm.Param('Range', w='SOUR:CURR:RANG', q='SOUR:CURR:RANG?', t='cont', pmin=-105e-3, pmax=105e3, units='A'))
        self.params.append(pm.Param('AutoRange', w='SOUR:WAVE:RANG BEST', t='act'))
        self.pnames = [p.name for p in self.params]