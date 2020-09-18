import Adafruit_DHT
from multiprocessing import Process, Value
from collections import defaultdict
import time
import ctypes
import sys

#import generic server model
from SensorServer import SensorServerClass

DHT_SENSOR = Adafruit_DHT.DHT22

class DHT22Sensor:
    DHT_MAXT                = 80
    DHT_MINT                = -40
    DHT_MAXH                = 100
    DHT_MINH                = 0
    
    def __init__(self, datapin, readFrequency, tHyst = 0, hHyst = 0):
        self.datapin                = datapin
        self.readFrequency          = readFrequency
        self.tempHyst               = tHyst
        self.humHyst                = hHyst
        self.temp                   = Value(ctypes.c_double, 0xdeadbeef) 
        self.hum                    = Value(ctypes.c_double, 0xdeadbeef)
        self.lastTemperatureTime    = Value(ctypes.c_double, 0xdeadbeef)
        self.lastHumidityTime       = Value(ctypes.c_double, 0xdeadbeef)

    @staticmethod
    def validTemperature(temp):
        return temp != None and temp >= DHT22Sensor.DHT_MINT and temp <= DHT22Sensor.DHT_MAXT

    @staticmethod
    def validHumidity(hum):
        return hum != None and hum >= DHT22Sensor.DHT_MINH and hum <= DHT22Sensor.DHT_MAXH
    
    def hasChangedTemp(self, temp):
        return temp <= (self.temp.value - self.tempHyst) or temp >= (self.temp.value + self.tempHyst)
    
    def hasChangedHum(self, hum):
        return hum <= (self.hum.value - self.humHyst) or hum >= (self.hum.value + self.humHyst)

    def read(self):
        humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, self.datapin)
        currentTime = time.time()

        self.temp.acquire()
        self.hum.acquire()
        self.lastTemperatureTime.acquire()
        self.lastHumidityTime.acquire()

        if DHT22Sensor.validTemperature(temperature):
            if self.temp.value == 0xdeadbeef:
                self.temp.value = temperature
            elif self.hasChangedTemp(temperature):
                self.temp.value = temperature
            self.lastTemperatureTime.value = currentTime
        
        if DHT22Sensor.validHumidity(humidity):
            if self.hum.value == 0xdeadbeef:
                self.hum.value = humidity
            elif self.hasChangedHum(humidity):
                self.hum.value= humidity
            self.lastHumidityTime.value = currentTime

        self.lastHumidityTime.release()
        self.lastTemperatureTime.release()
        self.hum.release()
        self.temp.release()

    def getTemp(self):
        self.temp.acquire()
        self.lastTemperatureTime.acquire()

        t = (self.temp.value, self.lastTemperatureTime.value)

        self.lastTemperatureTime.release()
        self.temp.release()
        return t

    def getHum(self):
        self.hum.acquire()
        self.lastHumidityTime.acquire()

        t = (self.hum.value, self.lastHumidityTime.value)

        self.lastHumidityTime.release()
        self.hum.release()
        return t

    def getData(self): 
        self.temp.acquire()
        self.hum.acquire()
        self.lastTemperatureTime.acquire() 
        self.lastHumidityTime.acquire()

        if int(self.lastTemperatureTime.value) == 0xdeadbeef or int(self.lastHumidityTime.value) == 0xdeadbeef:
            self.lastHumidityTime.release()
            self.lastTemperatureTime.release() 
            self.hum.release()
            self.temp.release()
            return None


        data = { 'temperature' : round(self.temp.value,3), 'humidity': round(self.hum.value,3), 'temperatureTimestamp': self.lastTemperatureTime.value, 'humidityTimestamp': self.lastHumidityTime.value}

        self.lastHumidityTime.release()
        self.lastTemperatureTime.release() 
        self.hum.release()
        self.temp.release()

        return data
    
    def startUpdater(self):
        self.updater = Process(target=self.__updateData, args=())
        self.updater.start()

    def stopUpdater(self):
        if self.updater.is_alive():
            self.updater.join()

    def __updateData(self):
        try:
            while True:
                self.read()
                time.sleep(self.readFrequency)
        except KeyboardInterrupt:
            sys.exit(0)

def main(arg):
    if len(arg) != 2:
        sensor = DHT22Sensor(21, 0, 0.05, 0.05)
        address = ('localhost', 12345)
    else:
        sensor_dict = defaultdict(int, arg[1])
        freq = 1 / sensor_dict['FREQUENCY']
        sensor = DHT22Sensor(sensor_dict['PIN'], freq, sensor_dict['T_HYST'], sensor_dict['H_HYST']) 
        address = ('localhost', sensor_dict['SERVER_PORT'])
    password = 'DHT22iscool'

    sensorServer = SensorServerClass(address, password, sensor)
    sensorServer.run()

if __name__ == "__main__":
    main(sys.argv)
