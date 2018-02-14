    # -*- coding: utf-8 -*-
""" 
.. module:: bitalino
   :synopsis: BITalino API

*Created on Fri Jun 20 2014*
"""

import platform
import math
import numpy
import re
import serial
import struct
import proses
import time
import thread
import biosppy
import matplotlib.pyplot as plt
from matplotlib import style
from Tkinter import *
from collections import deque

root = Tk()

def find():
    """
    :returns: list of (tuples) with name and MAC address of each device found
    
    Searches for bluetooth devices nearby.
    """
    if platform.system() == 'Windows' or platform.system() == 'Linux':
        import bluetooth
        nearby_devices = bluetooth.discover_devices(lookup_names=True)
        return nearby_devices
    else:
        raise Exception(ExceptionCode.INVALID_PLATFORM)

class ExceptionCode():
    INVALID_ADDRESS = "The specified address is invalid." 
    INVALID_PLATFORM= "This platform does not support bluetooth connection." 
    CONTACTING_DEVICE = "The computer lost communication with the device."      
    DEVICE_NOT_IDLE = "The device is not idle."        
    DEVICE_NOT_IN_ACQUISITION = "The device is not in acquisition mode." 
    INVALID_PARAMETER = "Invalid parameter."

class BITalino(object):
    """
    :param macAddress: MAC address or serial port for the bluetooth device
    :type macAddress: str
    :raises Exception: invalid MAC address or serial port
         
    Connects to the bluetooth device with the MAC address or serial port provided.
    
    Possible values for parameter *macAddress*:
    
    * MAC address: e.g. ``00:0a:95:9d:68:16``
    * Serial port - device name: depending on the operating system. e.g. ``COM3`` on Windows; ``/dev/tty.bitalino-DevB`` on Mac OS X; ``/dev/ttyUSB0`` on GNU/Linux.
    """
    def __init__(self, macAddress):
        regCompiled = re.compile('^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$');
        checkMatch = re.match(regCompiled, macAddress);
        if (checkMatch):
            if platform.system() == 'Windows' or platform.system() == 'Linux':
                import bluetooth
                self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
                self.socket.connect((macAddress, 1))
                self.serial = False     
            else:
                raise Exception(ExceptionCode.INVALID_PLATFORM)
        elif (macAddress[0:3] == 'COM' and platform.system() == 'Windows') or (macAddress[0:5] == '/dev/' and platform.system() != 'Windows'):
            self.socket = serial.Serial(macAddress, 115200)
            self.serial = True
        else:
            raise Exception(ExceptionCode.INVALID_ADDRESS)
        
        self.started = False
        self.macAddress = macAddress
    
    def start(self, SamplingRate = 1000, analogChannels = [0, 1, 2, 3, 4, 5]):
        """
        :param SamplingRate: sampling frequency (Hz)
        :type SamplingRate: int    
        :param analogChannels: channels to be acquired
        :type analogChannels: array, tuple or list of int
        :raises Exception: device already in acquisition (not IDLE)
        :raises Exception: sampling rate not valid
        :raises Exception: list of analog channels not valid
        
        Sets the sampling rate and starts acquisition in the analog channels set. 
        Setting the sampling rate and starting the acquisition implies the use of the method :meth:`send`.
        
        Possible values for parameter *SamplingRate*:
        
        * 1
        * 10
        * 100
        * 1000
        
        Possible values, types, configurations and examples for parameter *analogChannels*:
        
        ===============  ====================================
        Values           0, 1, 2, 3, 4, 5
        Types            list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   Any number of channels, identified by their value
        Examples         ``[0, 3, 4]``, ``(1, 2, 3, 5)``
        ===============  ====================================
        
        .. note:: To obtain the samples, use the method :meth:`read`.
        """    
        if (self.started == False):
            if int(SamplingRate) not in [1, 10, 100, 1000]:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
            
            if int(SamplingRate) == 1000:
                commandSRate = 3
            elif int(SamplingRate) == 100:
                commandSRate = 2
            elif int(SamplingRate) == 10:
                commandSRate = 1
            elif int(SamplingRate) == 1:
                commandSRate = 0
                            
            if isinstance(analogChannels, list):
                analogChannels = analogChannels
            elif isinstance(analogChannels, tuple):
                analogChannels = list(analogChannels)
            elif isinstance(analogChannels, numpy.ndarray):
                analogChannels = analogChannels.astype('int').tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)

            analogChannels = list(set(analogChannels))
            
            if len(analogChannels) == 0 or len(analogChannels) > 6 or any([item not in range(6) or type(item)!=int for item in analogChannels]):
                raise Exception(ExceptionCode.INVALID_PARAMETER)
            
            self.send((commandSRate << 6)| 0x03)
            
            commandStart = 1
            for i in analogChannels:
                commandStart = commandStart | 1<<(2+i)

            self.send((commandSRate << 6)| 0x03)
            self.send(commandStart)
            self.started = True
            self.analogChannels = analogChannels
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)
    
    def stop(self):
        """
        :raises Exception: device not in acquisition (IDLE)
        
        Stops the acquisition. Stoping the acquisition implies the use of the method :meth:`send`.
        """
        if (self.started):
            self.send(0)
            self.started = False
            self.version()
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)
    
    def close(self):
        """
        Closes the bluetooth or serial port socket.
        """
        self.socket.close()
    
    def send(self, data):
        """
        Sends a command to the BITalino device.
        """
        time.sleep(0.1)
        if self.serial:
            self.socket.write(chr(data))
        else:
            self.socket.send(chr(data))
    
    def battery(self, value=0):
        """
        :param value: threshold value
        :type value: int
        :raises Exception: device in acquisition (not IDLE)
        :raises Exception: threshold value is invalid
        
        Sets the battery threshold for the BITalino device. Setting the battery threshold implies the use of the method :meth:`send`.
        
        Possible values for parameter *value*:
        
        ===============  =======  =====================
        Range            *value*  Corresponding threshold (Volts)               
        ===============  =======  =====================
        Minimum *value*  0        3.4 Volts
        Maximum *value*  63       3.8 Volts
        ===============  =======  =====================
        """
        if (self.started == False):
            if 0 <= int(value) <= 63:
                commandBattery = int(value) << 2
                self.send(commandBattery)
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE)
    
    def trigger(self, digitalArray=[0, 0, 0, 0]):
        """
        :param digitalArray: array which acts on digital outputs according to the value: 0 or 1
        :type digitalArray: array, tuple or list of int
        :raises Exception: list of digital channel output is not valid
        :raises Exception: device not in acquisition (IDLE)
             
        Acts on digital output channels of the BITalino device. Triggering these digital outputs implies the use of the method :meth:`send`.
       
        Each position of the array *digitalArray* corresponds to a digital output, in ascending order. Possible values, types, configurations and examples for parameter *digitalArray*:

        ===============  ====================================
        Values           0 or 1
        Types            list ``[]``, tuple ``()``, array ``[[]]``
        Configurations   4 values, one for each digital channel output
        Examples         ``[1, 0, 1, 0]``: Digital 0 and 2 will be set to 1 while Digital 1 and 3 will be set to 0
        ===============  ====================================          
        """
        if (self.started):
            if isinstance(digitalArray, list):
                digitalArray = digitalArray
            elif isinstance(digitalArray, tuple):
                digitalArray = list(digitalArray)
            elif isinstance(digitalArray, numpy.ndarray):
                digitalArray = digitalArray.astype('int').tolist()
            else:
                raise Exception(ExceptionCode.INVALID_PARAMETER)
            
            pValues = [0, 1]
            if len(digitalArray) != 4 or any([item not in pValues or type(item)!=int for item in digitalArray]):
                raise Exception(ExceptionCode.INVALID_PARAMETER)
            
            data = 3
            for i,j in enumerate(digitalArray):
                data = data | j<<(2+i)
            self.send(data)
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)
    
    def read(self, nSamples=100):
        """
        :param nSamples: number of samples to acquire
        :type nSamples: int
        :returns: array with the acquired data 
        :raises Exception: device not in acquisition (in IDLE)
        :raises Exception: lost communication with the device
        
        Acquires `nSamples` from BITalino. Reading samples from BITalino implies the use of the method :meth:`receive`.
        
        Requiring a low number of samples (e.g. ``nSamples = 1``) may be computationally expensive; it is recommended to acquire batches of samples (e.g. ``nSamples = 100``).

        The data acquired is organized in a matrix whose lines correspond to samples and the columns are as follows:
        
        * Sequence Number
        * 4 Digital Channels (always present)
        * 1-6 Analog Channels (as defined in the :meth:`start` method)
        
        Example matrix for ``analogChannels = [0, 1, 3]`` used in :meth:`start` method:
        
        ==================  ========= ========= ========= ========= ======== ======== ========
        Sequence Number*    Digital 0 Digital 1 Digital 2 Digital 3 Analog 0 Analog 1 Analog 3              
        ==================  ========= ========= ========= ========= ======== ======== ========
        0                   
        1 
        (...)
        15
        0
        1
        (...)
        ==================  ========= ========= ========= ========= ======== ======== ========
        
        .. note:: *The sequence number overflows at 15 
        """
        if (self.started):
            nChannels = len(self.analogChannels)
            
            if nChannels <=4 :
                number_bytes = int(math.ceil((12.+10.*nChannels)/8.))
            else:
                number_bytes = int(math.ceil((52.+6.*(nChannels-4))/8.))
            
            dataAcquired = numpy.zeros((nSamples, 5 + nChannels))
            for sample in range(nSamples):
                Data = self.receive(number_bytes)
                decodedData = list(struct.unpack(number_bytes*"B ", Data))
                crc = decodedData[-1] & 0x0F
                decodedData[-1] = decodedData[-1] & 0xF0
                x = 0
                for i in range(number_bytes):
                    for bit in range(7, -1, -1):
                        x = x << 1
                        if (x & 0x10):
                            x = x ^ 0x03
                        x = x ^ ((decodedData[i] >> bit) & 0x01)
                if (crc == x & 0x0F):
                    dataAcquired[sample, 0] = decodedData[-1] >> 4
                    dataAcquired[sample, 1] = decodedData[-2] >> 7 & 0x01
                    dataAcquired[sample, 2] = decodedData[-2] >> 6 & 0x01
                    dataAcquired[sample, 3] = decodedData[-2] >> 5 & 0x01
                    dataAcquired[sample, 4] = decodedData[-2] >> 4 & 0x01
                    if nChannels > 0:
                        dataAcquired[sample, 5] = ((decodedData[-2] & 0x0F) << 6) | (decodedData[-3] >> 2)
                    if nChannels > 1:
                        dataAcquired[sample, 6] = ((decodedData[-3] & 0x03) << 8) | decodedData[-4]
                    if nChannels > 2:
                        dataAcquired[sample, 7] = (decodedData[-5] << 2) | (decodedData[-6] >> 6)
                    if nChannels > 3:
                        dataAcquired[sample, 8] = ((decodedData[-6] & 0x3F) << 4) | (decodedData[-7] >> 4)
                    if nChannels > 4:
                        dataAcquired[sample, 9] = ((decodedData[-7] & 0x0F) << 2) | (decodedData[-8] >> 6)
                    if nChannels > 5:
                        dataAcquired[sample, 10] = decodedData[-8] & 0x3F 
                else:
                    raise Exception(ExceptionCode.CONTACTING_DEVICE)
            return dataAcquired   
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IN_ACQUISITION)

    def version(self):
        """
        :returns: str with the version of BITalino 
        :raises Exception: device in acquisition (not IDLE)
        
        Retrieves the BITalino version. Retrieving the version implies the use of the methods :meth:`send` and :meth:`receive`.
        """       
        if (self.started == False):
            self.send(7)
            version_str = ''
            while True: 
                version_str += self.receive(1)
                if version_str[-1] == '\n' and 'BITalino' in version_str:
                    break
            return version_str[version_str.index("BITalino"):-1]
        else:
            raise Exception(ExceptionCode.DEVICE_NOT_IDLE) 
    
    def receive(self, nbytes):
        """
        :param nbytes: number of bytes to retrieve
        :type nbytes: int
        :return: string packed binary data
        
        Retrieves `nbytes` from the BITalino device and returns it as a string pack with length of `nbytes`.
        """
        
        reader = self.socket.read if self.serial else self.socket.recv
        data = ''
        while len(data) < nbytes:
            data += reader(1)
        return data
            
def convert(array):
    divisor = numpy.divide
    subtractor = numpy.subtract
    multiplier = numpy.multiply
    powerer = numpy.power

    n = 10
    vcc = 3.3
    half = 0.5
    g = 1100
    denominator = powerer(2,n)

    result = numpy.array([])
    result = divisor(array,denominator)
    result = subtractor(result,half)
    result = multiplier(result,vcc)
    result = divisor(result,g)
    result = multiplier(result,1000)

    return result

def dataPlotting():
    # Take time
    start = time.time()
    end = time.time()
    interval = end - start

    # Create Figure
    plt.figure()
    plt.title('ECG')
    plt.xlabel("n")
    plt.ylabel("Amplitude")

    # plt.figure(2)
    # plt.title('Bandpass Filter')
    # plt.xlabel("Time(sec)")
    # plt.ylabel("Amplitude")

    nData = numpy.array([])
    secg = numpy.array([])
    secg2 = numpy.array([])

    nDataPlot = numpy.array([])
    secgPlot = numpy.array([])
    secg2Plot = numpy.array([])


    summ = 0
    counter = 0

    # Optimizing Python
    cla=plt.cla
    draw=plt.draw
    timed = time.time
    appe = numpy.append
    plotted = plt.plot
    readed = device.read
    bandpass = ps.butter_bandpass_filter
    convArr = numpy.asarray
    segmen = biosppy.ecg.hamilton_segmenter
    cpeak = biosppy.ecg.correct_rpeaks
    norm = biosppy.signals.tools.normalize
    savetext = numpy.savetxt
    analitycSignal = biosppy.signals.tools.analytic_signal
    trans = numpy.transpose

    while (interval) < running_time:
        # Read samples
        data = readed(nSamples)
        dataT = data.T
        dataTbaru = convert(dataT[6])

        interval = end - start
        
        #secg = appe(secg,dataT[6])
        secg2 = appe(secg2,dataTbaru)
        nData = appe(nData,[counter + 1,counter + 2,counter + 3,counter + 4,counter + 5,counter + 6,counter + 7,counter + 8,counter + 9,counter + 10])
        bandpassed = bandpass(secg2,lowcut,highcut,samplingRate,order)
        normalized = convArr(norm(signal=bandpassed,ddof=1))[0]
        hilbert = convArr(analitycSignal(signal=normalized, N=samplingRate*running_time))
        amplitud = hilbert[0]
        phas = hilbert[1]
        counter = counter + 10
        end = timed()
        
        cla()
        #if counter % 30
        # try:
        #    thread.start_new_thread( blyat, (nData, secg, bandpassed, ) )
        # alizedexcept:
        #    print "Error: unable to start thread"
        # # 500
        # plt.figure(1)
        if counter < 500 :
            plotted(nData, normalized, color='red', alpha=0.5)
            plotted(nData, bandpassed, color='blue', alpha=0.5)
        else :
            plotted(nData[counter-500:], normalized[counter-500:], color='red', alpha=0.5)
            plotted(nData[counter-500:], bandpassed[counter-500:], color='blue', alpha=0.5)
            rpeaks, = segmen(signal=normalized, sampling_rate=samplingRate)
            rpeaks, = cpeak(signal=normalized, rpeaks=rpeaks, sampling_rate=samplingRate,tol=0.05)        

        print counter

        draw()
        plt.pause(0.0001)
            
    savetext("ecgRaw.csv", trans([nData,secg2]), fmt='%.3e',delimiter=",",header="ECG")
    savetext("ecgProcessed.csv", trans([nData,normalized]), fmt='%.3e',delimiter=",",header="ECG")
    savetext("ecgAmplitude.csv", trans([amplitud]), fmt='%.3e',delimiter=",",header="ECG")
    savetext("ecgPhase.csv", trans([phas]), fmt='%.3e',delimiter=",",header="ECG")
    savetext("peaks.csv", trans([rpeaks]), fmt='%.3e',delimiter=",",header="peaks")
    plt.savefig('ecg.png')

# def populateForSave(dataT, filtered_data, counter):
#     global secg
#     global nData
#     global secg2
#     appe = numpy.append
#     secg = appe(secg,dataT[6])
#     nData = appe(nData,[counter + 1,counter + 2,counter + 3,counter + 4,counter + 5,counter + 6,counter + 7,counter + 8,counter + 9,counter + 10])
#     secg2 = appe(secg2,filtered_data)

def startButton():
    # Start Acquisition
    device.start(samplingRate, acqChannels)

    dataPlotting()

    # Turn BITalino led on
    device.trigger(digitalOutput)

    # Stop acquisition
    device.stop()

def disconnectButton():
    # Close connection
    device.close()
    root.quit()


if __name__ == '__main__':
    macAddress = "98:D3:31:B2:BB:7D"
    running_time = 30

    batteryThreshold = 30
    acqChannels = [0,3]
    samplingRate = 100
    nSamples = 10
    digitalOutput = [0,0,1,1]
    lowcut = 0.5
    highcut = 40.0
    order = 2

    # Connect to BITalino
    device = BITalino(macAddress)

    # Create object
    ps = proses.ProcessECG()

    # Set battery threshold
    device.battery(batteryThreshold)
    
    # Read BITalino version
    print device.version()

    # Create GUI
    buttonStart = Button(root, text = "Start", command = startButton)
    buttonStart.pack(side=LEFT);

    buttonDc = Button(root, text = "Disconnect", command = disconnectButton)
    buttonDc.pack(side = LEFT)

    root.mainloop()
   
