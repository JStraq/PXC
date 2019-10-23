import re
import pyvisa

from . import Parameter as pm
from . import InstClass


# If you copy this file to make a new instrument, add it to lib/__init__.py!
# I'M DOING EVERYTHING IN TESLA-- MAKE SURE THE TESLA COMMAND HAS BEEN ACTIVATED!
class SLACMagnet(InstClass.Instrument):
    idnString = '-------> Commands:'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.teslaPerAmp = 0.151037
        self.maxField = 10  # Tesla
        self.switchTime = 60  # seconds
        self.stabTime = 30  # seconds
        self.writeDelay = 1
        self.visa.timeout = 500

        self.params.append(pm.Param('Output', q='GET OUTPUT', t='cont', comps=['Current', 'Voltage'], units=['A', 'V'],
                                    qmacro=lambda: self.getValue('OUTPUT')))
        self.params.append(pm.Param('Field', q='GET', t='cont', units='T', qmacro=self.getField))
        self.params.append(pm.Param('Ramp Rate', q='GET RATE', w='SET RATE', t='cont', units='T/s',
                                    qmacro=lambda: self.getValue('RATE'), wmacro=self.setRampRate))
        self.params.append(pm.Param('Voltage Limit', q='GET VL', t='cont', units='V',
                                    qmacro=lambda: self.getValue('VL')))
        self.params.append(pm.Param('Heater Voltage', q='GET HV', t='cont', units='V',
                                    qmacro=lambda: self.getValue('HV')))
        self.params.append(pm.Param('Field Midpoint', q='GET MID', w='SET MID', t='cont', units='T', pmin=0,
                                    pmax=self.maxField, qmacro=lambda: self.getValue('GET MID'),
                                    wmacro=lambda x: self.writeAck('SET MID', x)))
        self.params.append(pm.Param('Field Maximum', q='GET MAX', w='SET MAX', t='cont', units='T',
                                    qmacro=lambda: self.getValue('GET MAX'), wmacro=lambda x: self.writeAck('SET MAX', x)))

        self.params.append(pm.Param('Field Direction', q='GET SIGN', t='disc', vals=[0,1],
                                    labels=['POSITIVE', 'NEGATIVE'], qmacro=self.getSign))
        self.params.append(pm.Param('Set Field Direction', w='DIRECTION', t='disc', vals=['+', '-'],
                                    labels=['POSITIVE', 'NEGATIVE'], wmacro=lambda x: self.writeAck('DIRECTION', x)))

        self.params.append(pm.Param('Heater', w='HEATER', t='disc', vals=[0,1], labels=['OFF','ON'],
                                    wmacro=lambda x: self.writeAck('HEATER', x)))
        self.params.append(pm.Param('Magnet Mode', q='mode', t='disc', vals=[0, 1, 2, 3],
                                    labels=['DRIVEN', 'ZERO', 'SWITCHING','PERSISTENT'], qmacro=self.magMode))

        self.params.append(pm.Param('Ramp to Zero', w='RAMP ZERO', t='act', wmacro=lambda x: self.writeAck('RAMP ZERO', x)))
        self.params.append(pm.Param('Ramp to Mid', w='RAMP MID', t='act', wmacro=lambda x: self.writeAck('RAMP MID', x)))
        self.params.append(pm.Param('Ramp to Max', w='RAMP MAX', t='act', wmacro=lambda x: self.writeAck('RAMP MAX', x)))
        self.params.append(pm.Param('Ramp Status', q='RAMP STATUS', t='disc', vals=[0, 1, 2, 3, 4],
                                    labels=['HOLDING', 'RAMPING (CURRENT)', 'RAMPING (V LIMIT)', 'QUENCH', 'EXTERNAL'],
                                    qmacro=self.getRampStatus))

        self.params.append(pm.Param('Pause Ramp', w='PAUSE', t='disc', vals=[0, 1], labels=['OFF', 'ON'],
                           wmacro=lambda x: self.writeAck('PAUSE', x)))

        self.pnames = [p.name for p in self.params]

    def writeAck(self, register, val, *args):
        if val is not None:
            self.visa.write(register + ' ' + str(val))
        else:
            self.visa.write(register)
        try:
            print(self.visa.read())
        except pyvisa.errors.VisaIOError:
            pass

    def getRampStatus(self):
        ii = 0
        while ii<5:
            try:
                status = self.visa.query('RAMP STATUS').split(':')[1].strip()
                break
            except pyvisa.errors.VisaIOError:
                ii+=1
        keyword = status.split(' ')[0]
        if keyword == 'RAMPING':
            if status.split(' ')[-1] == 'VOLTS':
                keyword = 'RAMPING (V LIMIT)'
            else:
                keyword = 'RAMPING (CURRENT)'
        return [keyword]

    def getField(self):
        sign = '' if self.getSign()[0]=='POSITIVE' else '-'
        mode = self.magMode()[0]
        if mode == 'PERSISTENT':
            status = self.visa.query('GET PER')
            field = re.search('\d+\.\d+', status).group(0)
        else:
            status = self.visa.query('GET OUTPUT')
            field = re.search('\d+\.\d+', status).group(0)
        return [sign+field]

    def getValue(self, register, *args):
        status = self.visa.query('GET ' + register)
        status = status[10:]
        search = re.findall('\d+\.\d+', status)
        if search == []:
            search = re.findall('\d+', status)
        if register == 'OUTPUT':
            search[0] = '{:.4f}'.format(float(search[0])/self.teslaPerAmp)
        return search

    def getSign(self, *args):
        status = self.visa.query('GET SIGN').strip()
        status = status[-8:]
        return [status]

    def magMode(self):
        status = self.visa.query('HEATER')
        status = status.split(':')[1].strip()
        if status == 'ON':
            mode = 'DRIVEN'
        elif status == 'OFF':
            mode = 'ZERO'
        elif status == 'SWITCHING':
            mode = 'SWITCHING'
        else:
            mode = 'PERSISTENT'
        return [mode]

    def setRampRate(self, rate):
        rate_Ts = float(rate)
        rate_As = rate_Ts/self.teslaPerAmp
        self.visa.write('SET RAMP {:.4f}'.format(rate_As))
        print(self.visa.read())