from . import InstClass
from . import Parameter as pm


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Lakeshore340(InstClass.Instrument):
    idnString = 'LSCI,MODEL340'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 0.2

        self.params.append(pm.Param('TemperatureA', q='KRDG? A', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureB', q='KRDG? B', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureC1', q='KRDG? C1', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureC2', q='KRDG? C2', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureC3', q='KRDG? C3', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureC4', q='KRDG? C4', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureD1', q='KRDG? D1', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureD3', q='KRDG? D3', t='cont', units='K'))
        self.params.append(pm.Param('TemperatureD4', q='KRDG? D4', t='cont', units='K'))
        self.params.append(pm.Param('Setpoint1', w='SETP 1,', q='SETP? 1', t='cont', units='K'))
        self.params.append(pm.Param('Setpoint2', w='SETP 2,', q='SETP? 2', t='cont', units='K'))
        self.params.append(pm.Param('SetpointBoth', w='SETP,', t='cont', units='K', wmacro=lambda x: self.setpointBoth(x)))

        self.params.append(pm.Param('HeaterOutput', q='HTR?', t='cont', pmin=0, pmax=100, units='%'))
        self.params.append(pm.Param('HeaterStatus', q='HTRST?', t='disc', vals=range(3),
                                    labels=['No Error', 'Heater Open', 'Heater Short']))
        self.params.append(pm.Param('HeaterRange', w='RANGE', q='RANGE?', t='disc', vals=range(6),
                                    labels=['Off', '5mW', '50mW', '500mW', '5W', '50W']))
        self.params.append(pm.Param('Analog1Settings', q='ANALOG? 1', t='cont'))
        self.params.append(pm.Param('Analog2Settings', q='ANALOG? 2', t='cont'))
        self.params.append(pm.Param('AnalogOut1', q='AOUT? 1', t='cont', units='%'))
        self.params.append(pm.Param('AnalogOut2', q='AOUT? 2', t='cont', units='%'))
        self.params.append(pm.Param('ControlSettings 1', q='CSET? 1', t='cont'))
        self.params.append(pm.Param('ControlSettings 2', q='CSET? 2', t='cont'))

        labels = ['Manual PID', 'Zone', 'Open Loop', 'AutoTune PID', 'AutoTune PI', 'AutoTune P']
        self.params.append(pm.Param('LoopMode1', w='CMODE 1,', q='CMODE? 1', t='disc', vals=range(1,7), labels=labels))
        self.params.append(pm.Param('LoopMode2', w='CMODE 2,', q='CMODE? 2', t='disc', vals=range(1,7), labels=labels))

        self.params.append(pm.Param('Ramp1', w='RAMP 1, 1,', q='RAMP? 1', t='cont', pmax=100, pmin=0.1,
                                    comps=['RampStatus', 'RampRate'], units=['On?', 'K/min'], prec=1))
        self.params.append(pm.Param('Ramp2', w='RAMP 2, 1,', q='RAMP? 2', t='cont', pmax=100, pmin=0.1,
                                    comps=['RampStatus', 'RampRate'], units=['On?', 'K/min'], prec=1))
        self.params.append(pm.Param('Ramp1Off', w='RAMP 1,0', t='act'))
        self.params.append(pm.Param('Ramp2Off', w='RAMP 2,0', t='act'))

        self.params.append(pm.Param('PID1', w='PID 1', q='PID? 1,', t='cont', comps=['P1', 'I1', 'D1'], units='ul'))
        self.params.append(pm.Param('PID2', w='PID 2', q='PID? 2,', t='cont', comps=['P2', 'I2', 'D2'], units='ul'))

        self.pnames = [p.name for p in self.params]

    def setpointBoth(self, temp):
        for ii in (1,2):
            cmd = 'SETP {:d}, {:f}'.format(ii, float(temp))
            self.visa.write(cmd)
            print(cmd)