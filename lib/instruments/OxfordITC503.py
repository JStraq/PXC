from . import Parameter as pm
from . import InstClass
import pyvisa


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class OxfordITC503(InstClass.Instrument):
    idnString = 'X'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.visa.read_termination = '\r'
        self.visa.write_termination = '\r'
        self.writeDelay = 0.09
        self.visa.write('C1')
        self.visa.write('A1')
        self.visa.write('w')
        self.visa.read()
        
        try:
            self.visa.timeout = 500
            response = 'something'
            while response is not '':
                response = self.visa.read()
        except pyvisa.errors.VisaIOError:
            pass
            

        self.params.append(pm.Param('Temperature', q='R1', t='cont', units='K', qmacro=lambda: self.readValue('R1')))
        self.params.append(pm.Param('Setpoint', q='R0', w='T', t='cont', units='K', wmacro=lambda x: self.writeAck('T',x), qmacro=lambda: self.readValue('R0')))
        self.params.append(pm.Param('Set Sweep Temp', w='w', wmacro=self.setSweepTemp, t='cont', units='K'))
        self.params.append(pm.Param('Sweep Ramp Time', w='w', wmacro=self.setSweepRamp, t='cont', units='min'))
        self.params.append(pm.Param('Sweep Hold Time', w='w', wmacro=self.setSweepHold, t='cont', units='min'))
        self.params.append(pm.Param('Clear Sweep', w='w', t='act',wmacro=lambda x: self.writeAck('w','')))
        self.params.append(pm.Param('Stop Sweep', w='S0', t='act', wmacro=lambda x: self.writeAck('S', 0)))
        self.params.append(pm.Param('Start Sweep', w='S1', t='act', wmacro=lambda x: self.writeAck('S', 1)))
        self.params.append(pm.Param('Fill Sweep', w='ff', t='act', wmacro=lambda x: self.fillSweepTable(x)))
        self.params.append(pm.Param('Heater Power', q='R5', t='cont', units=r'%'))
        
        self.pnames = [p.name for p in self.params]

    def writeAck(self, command, val, *args):
        self.visa.write(command + str(val))
        self.visa.read()

    def readValue(self, command, *args):
        response = self.visa.query(command)
        response = response[1:]
        return [response]
        
    def setSweepTemp(self, val, *args):
        self.visa.write('x1')
        self.visa.read()
        self.visa.write('y1')
        self.visa.read()
        self.visa.write('s{:s}'.format(val))
        self.visa.read()
        print('SET SWEEP TEMP {:s}'.format(val))        
        
    def setSweepRamp(self, val, *args):
        self.visa.write('x1')
        self.visa.read()        
        self.visa.write('y2')
        self.visa.read()
        self.visa.write('s{:s}'.format(val))
        self.visa.read()
        print('SET SWEEP RAMP {:s}'.format(val))
    
    def setSweepHold(self, val, *args):
        self.visa.write('x1')
        self.visa.read()
        self.visa.write('y3')
        self.visa.read()
        self.visa.write('s{:s}'.format(val))
        self.visa.read()
        print('SET SWEEP TEMP {:s}'.format(val))
        
    def fillSweepTable(self, *args):
        for ii in range(2,15):        
            self.visa.write('x{:d}'.format(ii))
            self.visa.read()
            for jj in range(1,4):
                self.visa.write('y{:d}'.format(jj))
                self.visa.read()
                self.visa.write('s0')
                self.visa.read()