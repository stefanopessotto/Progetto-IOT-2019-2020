import RPi.GPIO as GPIO
from multiprocessing import Process, Value
from collections import defaultdict
import ctypes
import sys
import time

from SensorServer import SensorServerClass

class PIRSensor:

    def __init__(self, pin, frequency, calibrationTime = 0):
        self.dataPin            = pin
        self.startTime          = time.time() 
        self.calibrationTime    = calibrationTime
        self.valueReaded        = Value(ctypes.c_bool, False)
        self.readTime           = Value(ctypes.c_double, 0xdeadbeef)
        self.frequency          = frequency
        GPIO.setmode(GPIO.BCM)            #Set BCM pin enumeration
        GPIO.setup(self.dataPin, GPIO.IN)

    def read(self):
        if (time.time() - self.startTime) <= self.calibrationTime:  #PIR requires a calibration time
            return 

        self.valueReaded.acquire()
        self.readTime.acquire()

        self.valueReaded.value = (GPIO.input(self.dataPin) != GPIO.LOW)
        self.readTime.value = time.time()

        self.readTime.release()
        self.valueReaded.release()
    
    def getPosition(self):
        self.valueReaded.acquire()
        self.readTime.acquire()

        t = (self.valueReaded.value, self.readTime.value)

        self.readTime.release()
        self.valueReaded.release()
        return t

    def close(self):
        GPIO.cleanup()
    
    def getData(self):
        self.valueReaded.acquire()
        self.readTime.acquire()

        if int(self.readTime.value) == 0xdeadbeef: #Do not return data if nothing has been read yet
            self.readTime.release()
            self.valueReaded.release()
            return None

        data = { 'detection': self.valueReaded.value, 'timestamp': self.readTime.value }

        self.readTime.release()
        self.valueReaded.release()
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
        sensor = PIRSensor(pin=20, frequency=1)
        address = ('localhost', 12346)
    else:
        sensor_dict = defaultdict(int, arg[1])
        freq = 1 / float(sensor_dict['FREQUENCY'])
        sensor = PIRSensor(sensor_dict['PIN'], freq, sensor_dict['CALIBRATION_TIME'])
        address = ("localhost", sensor_dict['SERVER_PORT'])

    password = 'DHT22isbetter'
    sensorServer = SensorServerClass(address, password, sensor)
    sensorServer.run()
        

if __name__ == "__main__":
    main(sys.argv)
