from . import Parameter as pm
from . import InstClass
import pyvisa
import numpy as np
import re


# If you copy this file to make a new instrument, add it to lib/__init__.py!
class AH2550(InstClass.Instrument):
    idnString = 'MANUFACTURER'


    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.frequencies = np.array([50, 60, 70, 80, 100, 120, 140, 160, 200, 240, 300, 400,
                            500, 600, 700, 800, 1000, 1200, 1400, 1600, 2000, 2400,
                            300, 4000, 5000, 6000, 7000, 8000, 10000, 12000, 14,000,
                            16000, 20000])
        self.frequency = 1000
        self.visa.timeout=1500
        self.visa.read_termination = '\n'
        self.visa.write_termination = '\n'
        self.visa.write('FR 1000')
        self.visa.write('FIELD FREQUENCY ON')
        self.visa.write('FIELD V ON')
        self.visa.write('V 15')
                

        self.writeDelay = 0.09
        
        self.params.append(pm.Param('Bias', w='BI', t='disc', vals=['OF','IL','IH'], labels=['No Bias', '100 MOhm Series', '1 MOhm Series']))
        self.params.append(pm.Param('Commutation', w='COM', t='disc', vals=['OF','LINER','AS'], labels=['Sine Wave', 'Power Line Reject', 'Asynchronous']))
        self.params.append(pm.Param('Frequency', w='freq', q='freq', wmacro=self.wfreq, qmacro=self.qfreq, t='cont', units='Hz'))
        self.params.append(pm.Param('Capacitance and Loss', q='SI', qmacro=self.getCapLoss, t='cont', comps=['Capacitance', 'Loss'], units=['pF','loss']))
        self.params.append(pm.Param('Loss Units', w='UN', q='UN', t='disc', vals=['NS','DS','KO','GO','JP'], qmacro=self.getLossUnits,
                                    labels=['nS','Loss Tangent', 'Series, KOhms', 'Parallel, GOhms', 'G/omega, jpF']))
        self.params.append(pm.Param('Cap, Loss, Freq, Volt', q='SI', t='cont', qmacro=self.getCLFV, comps=['Capacitance', 'Loss', 'Bridge Freq', 'Bridge Voltage'],
                                    units=['pF', 'loss', 'Hz', 'V']))
        
        self.pnames = [p.name for p in self.params]
    
    def getLossUnits(self, *args):
        response = self.visa.query('SI')
        print(response)
        for un in ['NS','DS','KO','GO','JP']:
            if re.search(un, response) is not None:
                return [un]
        return ['Error']
    
    def getCapLoss(self, *args):
        failcount = 0
        done = False
        while not done and failcount < 10:
            try:
                self.visa.write('SI')
                response = self.visa.read()
                capstr = re.search(r'"C=",\s([0-9\.]+)', response).group(1)
                lossstr = re.search(r'"L=",\s([0-9\.]+)', response).group(1)
                print(response)
                print(capstr)
                print(lossstr)
                return [capstr, lossstr]    
            except AttributeError as e:
                print(e)
                print(response)
                failcount+=1
                print('AH failed to get the cap and loss--trying again')
        return ['0','0']
    
    def getCLFV(self, *args):
        self.visa.write('SI')
        response = self.visa.read()
        cap = re.search(r'C=\s([0-9\.]+)', response).group(1)
        loss = re.search(r'L=\s([0-9\.]+)', response).group(1)
        freq = re.search(r'F=\s([0-9\.]+)', response).group(1)
        volt = re.search(r'V=\s([0-9\.]+)', response).group(1)
        return [cap, loss, freq, volt]
        
    def nearFreq(self, freq):
        return self.frequencies[np.argmin(np.abs(self.frequencies-float(freq)))]
        
    def qfreq(self,*args):
        return [str(self.frequency)]
    
    def wfreq(self, freq, *args):
        print(freq)
        newfreq = self.nearFreq(freq)
        print(newfreq)
        self.frequency=newfreq
        print(self.frequency)
        self.visa.write('FR {:d}'.format(newfreq))
