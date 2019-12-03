from instruments import InstClass
from instruments import Parameter as pm
import re
import time


class SRS830(InstClass.Instrument):
    idnString = 'Stanford_Research_Systems,SR830'

    def __init__(self, apparatus, address, name=None):
        super().__init__(apparatus, address, name)
        self.writeDelay = 0.01

        self.params.append(pm.Param('SnapXY', q='SNAP? 1,2', t='cont', units=['V', 'V'], comps=['X', 'Y']))
        self.params.append(pm.Param('SnapRTheta', q='SNAP? 3,4', t='cont', units=['V', 'degrees'], comps=['R', 'Theta']))
        self.params.append(pm.Param('SnapXYNoise', q='SNAP? 10,11', t='cont', units=['V', 'V'], comps=['XNoise', 'YNoise']))

        self.params.append(pm.Param('Frequency', w='FREQ', q='FREQ?', t='cont', pmin=0.001, pmax=102e3, units='Hz'))
        self.params.append(pm.Param('Phase', w='PHAS', q='PHAS?', t='cont', pmin=-180, pmax=180, units='degrees'))
        self.params.append(pm.Param('AutoPhase', w='APHS', t='act'))
        self.params.append(pm.Param('AutoGain', w='AGAN', t='act'))
        self.params.append(pm.Param('Reserve', w='RMOD', q='RMOD?', t='disc', vals=range(3), labels=['High','Mid','Low']))
        self.params.append(pm.Param('FreqMode', w='FMOD', q='FMOD?', t='disc', vals=range(2), labels=['External','Internal']))
        self.params.append(pm.Param('Harmonic', w='HARM', q='HARM?', t='cont', pmin=1, pmax=19999))
        self.params.append(pm.Param('InputConfig', w='ISRC', q='ISRC?', t='disc', vals=range(4), labels=['A','A-B','1MOhm','100MOhm']))
        self.params.append(pm.Param('InputGround', w='IGND', q='IGND?', t='disc', vals=[0,1], labels=['Float','Ground']))
        self.params.append(pm.Param('InputCoupling', w='ICPL', q='ICPL?', t='disc', vals=[0,1], labels=['AC', 'DC']))

        labels = ['2 nV', '5 nV', '10 nV', '20 nV', '50 nV', '100 nV', '200 nV', '500 nV', '1 uV','2 uV', '5 uV', '10 uV',
                  '20 uV', '50 uV', '100 uV','200 uV', '500 uV', '1 mV','2 mV', '5 mV', '10 mV','20 mV', '50 mV', '100 mV',
                  '200 mV', '500 mV', '1 V',]
        self.params.append(pm.Param('Sensitivity', w='SENS', q='SENS?', t='disc', vals=range(27), labels=labels))

        labels = ['10 us', '30 us', '100 us', '300 us',
                  '1 ms', '3 ms', '10 ms', '30 ms', '100 ms', '300 ms',
                  '1 s', '3 s', '10 s', '30 s', '100 s', '300 s',
                  '1 ks', '3 ks', '10 ks', '30 ks']
        self.params.append(pm.Param('TimeConstant', w='OFLT', q='OFLT?', t='disc', vals=range(20), labels=labels))

        self.params.append(pm.Param('AutoOffsetX', w='AOFF 1', t='act', wmacro=lambda x: self.autoOffset(1)))
        self.params.append(pm.Param('AutoOffsetY', w='AOFF 2', t='act', wmacro=lambda x: self.autoOffset(2)))
        self.params.append(pm.Param('AutoOffsetR', w='AOFF 3', t='act', wmacro=lambda x: self.autoOffset(3)))

        self.params.append(pm.Param('OffsetExpandX', q='OEXP? 1', t='cont', comps=['XOffset', 'XExpand'], units=['%', '']))
        self.params.append(pm.Param('OffsetExpandY', q='OEXP? 2', t='cont', comps=['YOffset', 'YExpand'], units=['%', '']))
        self.params.append(pm.Param('OffsetExpandR', q='OEXP? 3', t='cont', comps=['ROffset', 'RExpand'], units=['%', '']))

        self.params.append(pm.Param('DisableOffsetExpandX', w='OEXP 1,0,0', t='act'))
        self.params.append(pm.Param('DisableOffsetExpandY', w='OEXP 2,0,0', t='act'))
        self.params.append(pm.Param('DisableOffsetExpandR', w='OEXP 3,0,0', t='act'))

        self.params.append(pm.Param('SetXExpand', w='OEXP 1', t='disc', vals=[0, 1, 2], labels=['0x', '10x', '100x'],
                                    wmacro=lambda x: self.offsetExpand(1, x)))
        self.params.append(pm.Param('SetYExpand', w='OEXP 2', t='disc', vals=[0, 1, 2], labels=['0x', '10x', '100x'],
                                    wmacro=lambda x: self.offsetExpand(2, x)))
        self.params.append(pm.Param('SetRExpand', w='OEXP 3', t='disc', vals=[0, 1, 2], labels=['0x', '10x', '100x'],
                                    wmacro=lambda x: self.offsetExpand(3, x)))

        self.params.append(pm.Param('ErrorRegister', q='ERRE?', t='cont', units='unitless'))
        self.params.append(pm.Param('StatusRegister', q='ERRS?', t='cont', units='unitless'))
        self.params.append(pm.Param('Reset', w='*RST', t='act'))
        self.params.append(pm.Param('AuxOut1', w='AUXV 1,', q='AUXV? 1', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut2', w='AUXV 2,', q='AUXV? 2', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut3', w='AUXV 3,', q='AUXV? 3', t='cont', pmin=-10.5, pmax=10.5, units='V'))
        self.params.append(pm.Param('AuxOut4', w='AUXV 4,', q='AUXV? 4', t='cont', pmin=-10.5, pmax=10.5, units='V'))

        labels = ['62.5 mHz', '125 mHz', ',250 mHz', '500 mHz', '1 Hz', '2 Hz', '4 Hz', '8 Hz',
                  '16 Hz', '32 Hz', '64 Hz', '128 Hz', '256 Hz', '512 Hz', 'Trigger']     
        self.params.append(pm.Param('SamplingRate', w='SRAT', q='SRAT?', t='disc', vals=range(15), labels=labels))
        self.params.append(pm.Param('StartSampling', w='STRT', t='act'))
        self.params.append(pm.Param('Trigger', w='TRIG', t='act'))
        self.params.append(pm.Param('TriggerStartMode', w='TSTR', q='TSTR?', t='disc', vals=[0,1], labels=['Off', 'On']))
        self.params.append(pm.Param('SamplingEndMode', q='SEND?', w='SEND', t='disc', vals=[0,1], labels=['One Shot', 'Loop']))
        self.params.append(pm.Param('PauseSampling', w='PAUS', t='act'))
        self.params.append(pm.Param('ResetSampleBuffer', w='REST', t='act'))
        self.params.append(pm.Param('SampledPoints', q='SPTS?', t='cont', units='points', prec=0))
        self.params.append(pm.Param('SampleForNSeconds', w='sample', t='cont', pmin=0.1, units='s', wmacro=self.readForTime))
        self.params.append(pm.Param('Buffer3s', q='buffer', t='cont', comps=['Buffer X', 'Buffer Y'], units=['V','V'], qmacro=self.readBuffer))
        self.params.append(pm.Param('Buffer3s_(Bytes)', q='buffer', t='cont', comps=['Buffer X', 'Buffer Y'], units=['V','V'], qmacro=self.readBuffer3B))
        self.params.append(pm.Param('Buffer1s', q='buffer', t='cont', comps=['Buffer X', 'Buffer Y'], units=['V','V'], qmacro=self.readBuffer1))
        

        self.pnames = [p.name for p in self.params]

    def readForTime(self, seconds, *args):
        self.visa.write('STRT')
        time.sleep(float(seconds))
        self.visa.write('PAUS')

    def readBuffer(self, *args):
        self.writeParam('Pause Sampling')
        total = int(float(self.readParam('Sampled Points')[0]))
        print('{:d} points in buffer'.format(total))
        N = 3*512 - 1
        if total-N > 0:
            start = total-N
        else:
            start = 0
            N = total-1
        self.visa.timeout = 10000
        self.visa.write('TRCL? 1,{:d},{:d}'.format(start, N))
        bufx = self.visa.read_raw()
        numx = []
        for bi in range(int(len(bufx)/4)):
            m = bufx[4*bi + 0] + 256*bufx[4*bi + 1]
            if m>0x7FFF:
                m -= 0x1000  # handle signed mantissa
            e = bufx[4*bi + 2] + 256*bufx[4*bi + 3]
            numx.append('{:.8g}'.format(m*2**(e-124)))
        bufx = '_'.join(numx)
        
        self.visa.write('TRCL? 2,{:d},{:d}'.format(start, N))
        bufy = self.visa.read_raw()
        numy = []
        for bi in range(int(len(bufy)/4)):
            if m>0x7FFF:
                m -= 0x1000  # handle signed mantissa
            m = bufy[4*bi + 0] + 256*bufy[4*bi + 1]
            e = bufy[4*bi + 2] + 256*bufy[4*bi + 3]
            numy.append('{:.8g}'.format(m*2**(e-124)))
        bufy = '_'.join(numy)
        
        self.writeParam('Reset Sample Buffer')
        return [bufx, bufy]
        
        
    def readBuffer3B(self, *args):
        self.writeParam('Pause Sampling')
        total = int(float(self.readParam('Sampled Points')[0]))
        print('{:d} points in buffer'.format(total))
        if total==0:
            return ['-', '-']  # something screwed up.
        N = 3*512 - 1
        if total-N > 0:
            start = total-N
        else:
            start = 0
            N = total-1
        self.visa.timeout = 10000
        self.visa.write('TRCL? 1,{:d},{:d}'.format(start, N))
        bufx = self.visa.read_raw()
        numx = []
        for bi in range(int(len(bufx)/4)):
            m = bufx[4*bi + 0] + 256*bufx[4*bi + 1]
            e = bufx[4*bi + 2] + 256*bufx[4*bi + 3]
            numx.append('{:04x}{:04x}'.format(e, m))
        bufx = ''.join(numx)
        
        self.visa.write('TRCL? 2,{:d},{:d}'.format(start, N))
        bufy = self.visa.read_raw()
        numy = []
        for bi in range(int(len(bufy)/4)):
            m = bufy[4*bi + 0] + 256*bufy[4*bi + 1]
            e = bufy[4*bi + 2] + 256*bufy[4*bi + 3]
            numy.append('{:04x}{:04x}'.format(e,m))
        bufy = ''.join(numy)
        
        self.writeParam('Reset Sample Buffer')
        return [bufx, bufy]
        
        
    def readBuffer1(self, *args):
        self.writeParam('Pause Sampling')
        total = int(float(self.readParam('Sampled Points')[0]))
        print('{:d} points in buffer'.format(total))
        N = 512 - 1
        if total-N > 0:
            start = total-N
        else:
            start = 0
            N = total-1
        self.visa.timeout = 10000
        self.visa.write('TRCL? 1,{:d},{:d}'.format(start, N))
        bufx = self.visa.read_raw()
        numx = []
        for bi in range(int(len(bufx)/4)):
            m = bufx[4*bi + 0] + 256*bufx[4*bi + 1]
            if m>0x7FFF:
                m -= 0x1000  # handle signed mantissa
            e = bufx[4*bi + 2] + 256*bufx[4*bi + 3]
            numx.append('{:.8g}'.format(m*2**(e-124)))
        bufx = '_'.join(numx)
        
        self.visa.write('TRCL? 2,{:d},{:d}'.format(start, N))
        bufy = self.visa.read_raw()
        numy = []
        for bi in range(int(len(bufy)/4)):
            if m>0x7FFF:
                m -= 0x1000  # handle signed mantissa
            m = bufy[4*bi + 0] + 256*bufy[4*bi + 1]
            e = bufy[4*bi + 2] + 256*bufy[4*bi + 3]
            numy.append('{:.8g}'.format(m*2**(e-124)))
        bufy = '_'.join(numy)
        
        self.writeParam('Reset Sample Buffer')
        return [bufx, bufy]
        
    def offsetExpand(self,channel,expand, *args):
        channelLUT = {1:'X', 2:'Y', 3:'R'}
        result = self.readParam('OffsetExpand'+channelLUT[channel])
        offset = result[0]
        cmd = 'OEXP {:d},{:s},{:s}'.format(channel, offset, expand)
        self.visa.write(cmd)
        print(cmd)

    def autoOffset(self, channel, *args):
        # in order to get an accurate read, of the offset, wait for 5 time constants
        tc = self.readParam('TimeConstant')
        timemults = {'us':1e-6, 'ms':1e-3, 's':1, 'ks': 1e3}
        label = self.getParam('TimeConstant').labels[int(tc[0].split(',')[0])]
        raw = re.search('([0-9]+) (.+)', label)
        delay = 5 * float(raw.group(1)) * timemults[raw.group(2)]
        time.sleep(delay)

        cmd = 'AOFF {:d}'.format(channel)
        self.visa.write(cmd)
        print(cmd)