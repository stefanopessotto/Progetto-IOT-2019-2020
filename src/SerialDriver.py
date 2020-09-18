from multiprocessing import Process, Value
from collections import defaultdict
import ctypes
import sys
import time
import serial
import json

from SensorServer import SensorServerClass

class SerialReader:

    def __init__(self, device, frequency, speed = 9600, parity = serial.PARITY_NONE, stopbits = serial.STOPBITS_ONE, blocksize = serial.EIGHTBITS, timeout = 1):
        self.device             = device 
        self.readValue          = Value(ctypes.c_int, 0xdeadbeef)
        self.readTime           = Value(ctypes.c_double, 0xdeadbeef)
        self.frequency          = frequency
        self.speed              = speed
        self.parity             = parity
        self.stopbits           = stopbits
        self.blocksize          = blocksize
        self.timeout            = timeout
        #init serial module
        self.serial_module      = serial.Serial(port = self.device, baudrate = self.speed, parity = self.parity, stopbits = self.stopbits, bytesize = self.blocksize, timeout = self.timeout)


    def read(self):
        acquired = 0
        try:
            msg = self.serial_module.readline().decode().rstrip("\n")
            readDict = json.loads(msg)
    
            self.readValue.acquire()
            acquired = 1
            self.readTime.acquire()
            acquired = 2
    
            self.readValue.value = readDict['Potentiometer']
            self.readTime.value = time.time() 
    
            self.readTime.release()
            self.readValue.release()
    
        except (UnicodeDecodeError,json.decoder.JSONDecodeError):
            print('malformed message from serial', file=sys.stderr)
            #free locks
            if acquired > 1:
                self.readTime.release()
            if acquired > 0:
                self.readValue.release()
        except (serial.SerialException,serial.serialutil.SerialException, KeyError) :
            print('Serial device disconnected', file=sys.stderr)
            #try to reconnect
            try:
                self.serial_module = serial.Serial(port = self.device, baudrate = self.speed, parity = self.parity, stopbits = self.stopbits, bytesize = self.blocksize, timeout = self.timeout)
                time.sleep(1)
            except Exception: 
                print('Cannot find serial device', file=sys.stderr)
    
    def getValue(self):
        self.readValue.acquire()
        self.readTime.acquire()
    
        t = (self.readValue.value, self.readTime.value)
    
        self.readTime.release()
        self.readValue.release()
        return t
    
    def close(self):
        self.serial_module.close()
    
    def getData(self):
        self.readValue.acquire()
        self.readTime.acquire()
    
        if int(self.readTime.value) == 0xdeadbeef:
            self.readTime.release()
            self.readValue.release()
            return None
        data = { 'potentiometer': self.readValue.value, 'timestamp': self.readTime.value }
    
        self.readTime.release()
        self.readValue.release()
        return data
                
    def startUpdater(self):
        self.updater = Process(target=self.__updateData, args=())
        self.updater.start()
    
    def stopUpdater(self):
        if self.updater.is_alive():
            self.updater.join()
        self.close()
                
    def __updateData(self):
        try:
            while True:
                self.read()
                time.sleep(self.frequency)
        except KeyboardInterrupt:
            sys.exit(0)

def main(arg):
    if len(arg) != 2:
        driver = SerialReader('/dev/ttyACM0', frequency=3)
        address = ('localhost', 12347)
    else:
        sensor_dict = defaultdict(int, arg[1])
        freq = 1 / float(sensor_dict['FREQUENCY'])
        driver = SerialReader(sensor_dict['DEVICE'], freq, sensor_dict['SPEED'], sensor_dict['PARITY'], sensor_dict['STOPBITS'], sensor_dict['COMMSIZE'], sensor_dict['TIMEOUT'])
        address = ('localhost', sensor_dict['SERVER_PORT'])

    password = 'Serialiscool'
    sensorServer = SensorServerClass(address, password, driver)
    sensorServer.run()
        

if __name__ == "__main__":
    main(sys.argv)
