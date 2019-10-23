from lib.instruments import InstClass
from lib.instruments import Parameter as pm
import re
import time


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class SRS865(InstClass.Instrument):
    idnString = 'Stanford_Research_Systems,SR865'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 1

        self.params.append(pm.Param('SnapXY', q='SNAP? 1,2', t='cont', units=['V', 'V'], comps=['X', 'Y']))
        self.params.append(pm.Param('SnapRTheta', q='SNAP? 3,4', t='cont', units=['V', 'degrees'], comps=['R', 'Theta']))
        self.params.append(pm.Param('AutoPhase', w='APHS', t='act'))
        self.params.append(pm.Param('AutoRange', w='ARNG', t='act'))
        self.params.append(pm.Param('AutoScale', w='ASCL', t='act'))
        self.params.append(pm.Param('FrequencyInternal', w='FREQINT', q='FREQINT?', t='cont', pmin=0.001, pmax=500e3, units='Hz'))
        self.params.append(pm.Param('FrequencyExternal', q='FREQEXT ?', t='cont', pmin=0.001, pmax=500e3, units='Hz'))
        self.params.append(pm.Param('Phase', w='PHAS', q='PHAS?', t='cont', pmin=-180, pmax=180, units='degrees'))
        self.params.append(pm.Param('OutputLevel', w='SLVL', q='SLVL?', t='cont', pmin=1e-9, pmax=2, units='V'))
        self.params.append(pm.Param('OutputOffset', w='SOFF', q='SOFF?', t='cont', pmin=-5, pmax=5, units='V'))
        self.params.append(pm.Param('SineOutMode', w='REFM', q='REFM', t='disc', labels=['Common', 'Difference'], vals=[0,1]))

        labels = ['1 V', '500 mV', '200 mV', '100 mV', '50 mV', '20 mV', '10 mV', '5 mV', '2 mV', '1 mV',
                  '500 uV', '200 uV', '100 uV', '50 uV', '20 uV', '10 uV', '5 uV', '2 uV', '1 uV', '500 nV',
                  '200 nV', '100 nV', '50 nV', '20 nV', '10 nV', '5 nV', '2 nV']
        self.params.append(pm.Param('Sensitivity', w='SCAL', q='SCAL?', t='disc', vals=range(28), labels=labels))

        labels = ['1 us', '3 us', '10 us', '30 us', '100 us', '300 us',
                  '1 ms', '3 ms', '10 ms', '30 ms', '100 ms', '300 ms',
                  '1 s', '3 s', '10 s', '30 s', '100 s', '300 s',
                  '1 ks', '3 ks', '10 ks', '30 ks']
        self.params.append(pm.Param('TimeConstant', w='OFLT', q='OFLT?', t='disc', vals=range(22), labels=labels))

        self.params.append(pm.Param('AutoOffsetX', w='OAUT 0', t='act', wmacro=lambda x: self.autoOffset(1)))
        self.params.append(pm.Param('AutoOffsetY', w='OAUT 1', t='act', wmacro=lambda x: self.autoOffset(2)))
        self.params.append(pm.Param('AutoOffsetR', w='OAUT 2', t='act', wmacro=lambda x: self.autoOffset(3)))

        self.params.append(pm.Param('OffsetX', w='COFA 0 ON;COFP 0', q='COFP? 0', t='cont', comps=['XOffset', 'XExpand'], units=['%', '']))
        self.params.append(pm.Param('OffsetY', w='COFA 1 ON;COFP 1', q='COFP? 1', t='cont', comps=['YOffset', 'YExpand'], units=['%', '']))
        self.params.append(pm.Param('OffsetR', w='COFA 2 ON;COFP 2', q='COFP? 2', t='cont', pmin=-999.99, pmax=999.99, units='%'))

        self.params.append(pm.Param('ExpandX', w='CEXP 0', q='CEXP? 0', t='disc', vals=[0,1,2], labels=['off', 'x10', 'x100']))
        self.params.append(pm.Param('ExpandY', w='CEXP 1', q='CEXP? 1', t='disc', vals=[0,1,2], labels=['off', 'x10', 'x100']))
        self.params.append(pm.Param('ExpandR', w='CEXP 2', q='CEXP? 2', t='disc', vals=[0,1,2], labels=['off', 'x10', 'x100']))

        self.params.append(pm.Param('DisableOffsetX', w='COFA 0 OFF', t='act'))
        self.params.append(pm.Param('DisableOffsetY', w='COFA 0 OFF', t='act'))
        self.params.append(pm.Param('DisableOffsetR', w='COFA 0 OFF', t='act'))

        self.params.append(pm.Param('AuxOut1', w='AUXV 0', q='AUXV? 0', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut2', w='AUXV 1', q='AUXV? 1', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut3', w='AUXV 2', q='AUXV? 2', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut4', w='AUXV 3', q='AUXV? 3', t='cont', pmin=-10.5, pmax=10.5, units='V'))


        self.params.append(pm.Param('SnapXYNoise', q='SNAP? 10,11', t='cont', units=['V', 'V'], comps=['XNoise', 'YNoise']))
        self.params.append(pm.Param('FreqMode', w='FMOD', q='FMOD?', t='disc', vals=range(2), labels=['External', 'Internal']))
        self.params.append(pm.Param('Harmonic', w='HARM', q='HARM?', t='cont', pmin=1, pmax=19999))
        self.params.append(pm.Param('HarmonicDual', w='HARMDUAL', q='HARMDUAL?', t='cont', pmin=1, pmax=19999))
        self.params.append(pm.Param('InputConfig', w='ISRC', q='ISRC?', t='disc', vals=[0,1],
                                    labels=['A', 'A-B']))
        self.params.append(pm.Param('InputGround', w='IGND', q='IGND?', t='disc', vals=[0, 1], labels=['Float', 'Ground']))
        self.params.append(pm.Param('InputCoupling', w='ICPL', q='ICPL?', t='disc', vals=[0, 1], labels=['AC', 'DC']))
        self.params.append(pm.Param('Reset', w='*RST', t='act'))

        self.pnames = [p.name for p in self.params]

    def autoOffset(self, channel, *args):
        # in order to get an accurate read, of the offset, wait for 5 time constants
        tc = self.readParam('TimeConstant')
        timemults = {'us':1e-6, 'ms':1e-3, 's':1, 'ks': 1e3}
        label = self.getParam('TimeConstant').labels[int(tc[0].split(',')[0])]
        raw = re.search('([0-9]+) (.+)', label)
        delay = 5 * float(raw.group(1)) * timemults[raw.group(2)]
        time.sleep(delay)

        cmd = 'OAUT {:d}'.format(channel)
        self.visa.write(cmd)
        print(cmd)