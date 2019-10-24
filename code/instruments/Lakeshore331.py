from . import InstClass
from . import Parameter as pm


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Lakeshore331(InstClass.Instrument):
    idnString = 'LSCI,MODEL331'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 0.09

        self.params.append(pm.Param('HeaterOutput', q='HTR?', t='cont', units='%'))
        self.params.append(pm.Param('HeaterStatus', q='HTRST?', t='disc', vals=range(3),
                                    labels=['No Error', 'Heater Open', 'Heater Short']))
        self.params.append(pm.Param('HeaterRange', w='RANGE', q='RANGE?', t='disc', vals=range(4),
                                    labels=['Off', 'Low', 'Medium', 'High']))
        self.params.append(pm.Param('AnalogOutput', q='AOUT?', t='cont', units='%'))
        self.params.append(pm.Param('PID_VTI', w='PID 1', q='PID? 1,', t='cont',
                                    comps=['P1', 'I1', 'D1'], units=['ul', 'ul', 'ul']))
        self.params.append(pm.Param('PID_Probe', w='PID 2', q='PID? 2,', t='cont',
                                    comps=['P2', 'I2', 'D2'], units=['ul', 'ul', 'ul']))
        self.params.append(pm.Param('Ramp_VTI', w='RAMP 1, 1', q='RAMP? 1', t='cont', pmax=100, pmin=0.1,
                                    comps=['RampStatus', 'RampRate'], units=['On?', 'K/min']))
        self.params.append(pm.Param('Ramp_Probe', w='RAMP 2, 1', q='RAMP? 2', t='cont', pmax=100, pmin=0.1,
                                    comps=['RampStatus', 'RampRate'], units=['On?', 'K/min']))
        self.params.append(pm.Param('RampOff_VTI', w='RAMP 1,0', t='act'))
        self.params.append(pm.Param('RampOff_Probe', w='RAMP 2,0', t='act'))
        self.params.append(pm.Param('Temperature_Probe', q='KRDG? A', t='cont', units='K'))
        self.params.append(pm.Param('Temperature_VTI', q='KRDG? B', t='cont', units='K'))
        self.params.append(pm.Param('Setpoint_VTI', w='SETP 1,', q='SETP? 1', t='cont', units='K'))
        self.params.append(pm.Param('Setpoint_Probe', w='SETP 2,', q='SETP? 2', t='cont', units='K'))

        self.pnames = [p.name for p in self.params]
