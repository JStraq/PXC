from . import Parameter as pm
from . import InstClass

# If you copy this file to make a new instrument, add it to lib/__init__.py!
class Keithley2230G(InstClass.Instrument):
    idnString = 'Keithley instruments, 2230G-30-1'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        
        self.params.append(pm.Param('Set V1', w='SOUR:APPL ch1,', t='cont', pmin=0,pmax=30,units='V'))
        self.params.append(pm.Param('Set V2', w='SOUR:APPL ch2,', t='cont', pmin=0,pmax=30,units='V'))
        self.params.append(pm.Param('Set V3', w='SOUR:APPL ch3,', t='cont', pmin=0,pmax=6,units='V'))
        self.params.append(pm.Param('Set extension', w='extend', wmacro=self.extend, t='cont', pmin=-100,pmax=100,units='%'))
        self.params.append(pm.Param('V1', q='SOUR:APPL? ch1', qmacro=self.Vch1, t='cont', pmin=0,pmax=30,units='V'))
        self.params.append(pm.Param('V2', q='SOUR:APPL? ch2', qmacro=self.Vch2, t='cont', pmin=0,pmax=30,units='V'))
        self.params.append(pm.Param('V3', q='SOUR:APPL? ch3', qmacro=self.Vch3, t='cont', pmin=0,pmax=6,units='V'))
        self.params.append(pm.Param('OutputStatus', w='OUTP:STAT:ALL', q='OUTP:STAT:ALL?', t='disc', vals=[0,1], labels=['Disabled', 'Enabled']))
        self.pnames = [p.name for p in self.params]
		
    def Vch1(self):
        response = self.visa.query('SOUR:APPL? ch1')
        print(response)
        response = response.strip().split(', ')
        print(response)
        return [response[0]]
		
    def Vch2(self):
        response = self.visa.query('SOUR:APPL? ch2')
        response = response.strip().split(', ')
        return [response[0]]

    def Vch3(self):
        response = self.visa.query('SOUR:APPL? ch3')
        response = response.strip().split(', ')
        return [response[0]]
        
    def extend(self, percent, *args):
        percent = float(percent)
        percent = max(min(100, percent), -100)
        percent = percent/100
        v1,v2,v3 = 0,0,0
        if percent>0:
            v2 = 0
            v1 = 0.025 + 7*percent
            v3 = 0.6*percent
        else:
            v1 = 0.025
            v2 = -7*percent
            v3 = -0.6*percent
        self.visa.write('SOUR:APPL ch1, {:.3f}'.format(v1))
        self.visa.write('SOUR:APPL ch2, {:.3f}'.format(v2))
        self.visa.write('SOUR:APPL ch3, {:.3f}'.format(v3))
        