from instruments import InstClass
from instruments import Parameter as pm
import re
import time
import pyvisa


# If you copy this file to make a new instrument, add it to lib/__init__.py!
# THESE BUGGERS ARE MESSY.
# They don't respond to *IDN commands, and the 5210 even completely locks up when it gets one of those.
# Important config notes:
#  - Start by setting the GPIB address (GPIB Parameter 0 on front panel) greater than 20: the apparatus code will then never send *IDN.
#  - Set the delimiter (GPIB parameter 1) to 2, which sets the terminator to the more modern CRLF
#  - Send a 'DD 44' command to make sure the delimiter between values in the XY command (for example) is a comma.

class SR5210(InstClass.Instrument):
    idnString = '5210'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 10

        self.params.append(pm.Param('Read XY', q='XY', t='cont', units=['V', 'V'], comps=['X', 'Y'], qmacro=self.quads))
        self.params.append(pm.Param('Read RTheta', q='MP', t='cont', units=['V', 'degrees'], comps=['R', 'Theta'], qmacro=self.magphase))
        self.params.append(pm.Param('Auto Sensitivity', w='AS', t='act', wmacro=self.autosens))
        self.params.append(pm.Param('Auto Phase', w='AQN', t='act'))
        self.params.append(pm.Param('Auto Tune Filter', w='ATS', t='act'))
        self.params.append(pm.Param('Auto Offset', w='AXO', t='act'))
        self.params.append(pm.Param('Line Filter', w='LF', q='LF', t='disc', vals=range(4), labels=['Off', '60 Hz', '120 Hz', '60 Hz and 120 Hz']))
        self.params.append(pm.Param('Reference Source', w='IE', q='IE', t='disc', vals=range(2), labels=['External (REF IN)', 'Internal']))
        self.params.append(pm.Param('Output Filter Slope', w='XDB', q='XDB', t='disc', vals=range(2), labels=['6 dB/octave', '12 dB/octave']))
        self.params.append(pm.Param('Harmonic Mode', w='F2F', q='F2F', t='disc', vals=range(2), labels=['Fundamental', '2nd Harmonic']))
        self.params.append(pm.Param('Reference Phase', w='P', q='P', t='cont', wmacro=self.wphase, qmacro=self.qphase, units='degrees'))
        self.params.append(pm.Param('Oscillator Frequency', w='OF', q='OF', t='cont', wmacro=self.wfreq,
                                    qmacro=self.qfreq, units='Hz', pmin=0.5, pmax=120e3))
        self.params.append(pm.Param('Oscillator Amplitude', w='OA', q='OA', t='cont', units='mVrms', pmin=0, pmax=2000))
                
        labels = ['100 nV', '300 nV', '1 uV', '3 uV', '10 uV', '30 uV', '100 uV','300 uV', '1 mV','3 mV',
                  '10 mV', '30 mV', '100 mV', '300 mV', '1 V', '3 V']
        self.params.append(pm.Param('Sensitivity', w='SEN', q='SEN', t='disc', vals=range(16), labels=labels))

        labels = ['Min', '1 ms', '3 ms', '10 ms', '30 ms', '100 ms', '300 ms',
                  '1 s', '3 s', '10 s', '30 s', '100 s', '300 s',
                  '1 ks', '3 ks']
        self.params.append(pm.Param('TimeConstant', w='TC', q='TC', t='disc', vals=range(len(labels)), labels=labels))
        self.params.append(pm.Param('Input Filter', w='FLT', q='FLT', t='disc', vals=range(4), labels=['Flat','Notch','Low Pass','Band Pass']))
        self.params.append(pm.Param('Frequency Tuning', w='ATC', t='disc', vals=range(2), labels=['Manual', 'Automatic']))
        self.params.append(pm.Param('Dynamic Reserve', w='DR', t='disc', vals=range(3), labels=['High Stability', 'Normal', 'High Resolution']))
        self.params.append(pm.Param('X Offset', w='XOF', t='disc', vals=range(2), labels=['Off', 'On']))
        self.params.append(pm.Param('Y Offset', w='YOF', t='disc', vals=range(2), labels=['Off', 'On']))

        self.pnames = [p.name for p in self.params]

    def qphase(self, *args):
        n1n2 = self.visa.query('P')
        quadrant, angle = n1n2.split(',')
        quadrant = float(quadrant)*90
        phase = str(float(angle)/100 + quadrant)
        return [phase]

    def wphase(self, phase, *args):
        phase = float(phase)
        n1 = int(phase // 90)
        n2 = phase - (n1*90)
        n2 *= 100   # convert to millidegrees
        n2 = int(n2)
        self.visa.write('P {:d}, {:d}'.format(n1,n2))

    def wfreq(self, freq, *args):
        freq = float(freq)
        lut = [2, 20, 200, 2e3, 2e4]
        n2 = sum([1 if freq>x else 0 for x in lut])
        n1 = int(freq / 10**(n2-4))

        print(n1,n2)
        self.visa.write('OF {:d} {:d}'.format(n1, n2))

    def qfreq(self, *args):
        n1, n2 = self.visa.query('OF').split(',')
        n1 = int(n1)
        n2 = int(n2)
        freq = n1 * 10**(n2-4)
        print(n1,n2)
        return [str(freq)]

    def quads(self, *args):
        sen, scale = self.readParam('Sensitivity')[0].split(',')[-1].strip().split(' ')
        maglookup = {'nV': 1e-9, 'uV': 1e-6, 'mV': 1e-3, 'V': 1}
        sen = float(sen) * maglookup[scale]
        xy = self.visa.query('MP')
        xx, yy = xy.split(',')
        xx = '{:.5f}'.format(float(xx) * sen / 1e5)
        yy = '{:.5f}'.format(float(yy) * sen / 1e5)
        return [xx, yy]

    def magphase(self, *args):
        sen, scale = self.readParam('Sensitivity')[0].split(',')[-1].strip().split(' ')
        maglookup = {'nV':1e-9, 'uV':1e-6, 'mV':1e-3, 'V':1}
        sen=float(sen)*maglookup[scale]
        mp = self.visa.query('MP')
        mag, phase = mp.split(',')
        mag = '{:.5f}'.format(float(mag) * sen/1e5)
        phase = '{:.5f}'.format(float(phase)/1000)
        return [mag, phase]

    def autosens(self, *args):
        self.visa.write('AS')
        done=False
        for ii in range(50):
            time.sleep(0.2)
            try:
                sb = int(self.visa.query('ST'))
                done = True
            except pyvisa.errors.VisaIOError:
                done = False
            if done:
                break
