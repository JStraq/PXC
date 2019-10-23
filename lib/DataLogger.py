# -*- coding: utf-8 -*-
"""
Created on Thu Sep  8 14:42:47 2016

@author: Joshua
"""
import datetime as dt
import os
import xml.etree.ElementTree as et
from xml.dom import minidom as md

class DataLogger:
    '''
    This class controls how data is taken
    '''
    def __init__(self, user, project, sample):
        # Generate path and file name
        self.folder = os.path.join('C:\\Data', user, project)
        self.starttime = dt.datetime.now()
        self.name= '{:s}_{:s}_{:s}_{:s}'.format(user,project,sample,self.starttime.strftime('%Y-%m-%d__%H-%M-%S'))
        self.path = os.path.join(self.folder, self.name)
        self.dataFile = None
        self.configFile = None
        self.seqFile = None
    
    def startLog(self, apparatus, metadata):
        # Create the folder if it doesn't exist
        if not os.path.exists(self.folder):
            os.makedirs(self.folder)

        # Create the three necessary files for logging the experiment.
        ## DATA: a tab-delimited *.dat file, one line of headers followed by columns of data
        ## CONFIG: a heirarchical *.xml file containing the active instruments and their configurations
        ## SEQ: another *.xml file describing the sequence as it was run.
        self.dataFile = open('{:s}_DATA.dat'.format(self.path), 'a+')
        self.configFile = open('{:s}_CONFIG.xml'.format(self.path), 'a+')
        self.seqFile = open('{:s}_SEQ.xml'.format(self.path), 'a+')
        
        exp = et.Element('experiment')
        
        desc = et.SubElement(exp,'description')
        et.SubElement(desc,'user').text(metadata['user'])
        et.SubElement(desc,'project').text(metadata['project'])
        et.SubElement(desc,'sample').text(metadata['sample'])
        et.SubElement(desc,'comment').text(metadata['comment'])
        
        tcsElem = et.SubElement(exp, 'temperature controller')
        for tc in apparatus.listTcs():
            a = et.SubElement(tcsElem, tc.name(), {'model':tc.model()})
            settings = tc.getSettings()
            for setting in settings.keys():
                b = et.SubElement(a, setting)
                b.text = settings[setting]
                    
        excsElem = et.SubElement(exp, 'excitation sources')
        for exc in apparatus.listExcs():
            a = et.SubElement(excsElem, exc.name(), {'model':exc.model()})
            settings = exc.getSettings()
            for setting in settings.keys():
                b = et.SubElement(a, setting)
                b.text = settings[setting]
                    
        measElem = et.SubElement(exp, 'measurement devices')
        for meas in apparatus.listMeas():
            a = et.SubElement(measElem, meas.name(), {'model':meas.model()})
            settings = meas.getSettings()
            for setting in settings.keys():
                b = et.SubElement(a, setting)
                b.text = settings[setting]
                
        reparsed = md.parseString(et.tostring(exp, 'utf-8'))
        self.configFile.write(reparsed.toprettyxml(indent="  "))
        self.configFile.close()
        
        # Write the headers into 
    
    def endLog(self, abort=False):
        self.dataFile.close()
        self.seqFile.close()
        #maybe add end-time to config file?            
    
    def saveData(self, data):
        raise NotImplementedError()
        
    def logSequence(self, seqCommand):
        seqElem = et.Element('command')
        params = seqCommand.listParams()
        for param in params:
            a = et.SubElement(seqElem, param)
            a.text = params[param]
        
        reparsed = md.parseString(et.tostring(seqElem, 'utf-8'))
        self.configFile.write(reparsed.toprettyxml(indent="  "))
        
    
    def loadVariable(self, var):
        raise NotImplementedError()