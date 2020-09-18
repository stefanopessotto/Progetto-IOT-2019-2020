import board
import busio
from oled_text import OledText, SmallLine, BigLine
from multiprocessing import Process, Value
import ctypes
import time
import sys

from SensorClient import SensorClient

class SSD1306_I2C:
    
    def __init__(self, height = 64, width = 128, pageTime = 1):
        self.i2c                        = busio.I2C(board.SCL, board.SDA)
        self.height                     = height
        self.width                      = width
        self.oled                       = OledText(self.i2c, self.width, self.height)
        self.pageTime                   = pageTime
        self.oled.auto_show             = False                                 #disable auto write on oled_text module
        self.lastDetection              = Value(ctypes.c_bool, False)
        self.lastTime                   = Value(ctypes.c_double, 0xdeadbeef) 
        self.lastTemperature            = Value(ctypes.c_double, 0xdeadbeef) 
        self.lastHumidity               = Value(ctypes.c_double, 0xdeadbeef)
        self.lastTempUpdate             = Value(ctypes.c_double, 0xdeadbeef)
        self.lastHumUpdate              = Value(ctypes.c_double, 0xdeadbeef)
        self.lastPotentiometer          = Value(ctypes.c_int, 0xdeadbeef)
        self.lastPotentiometerUpdate    = Value(ctypes.c_double, 0xdeadbeef)
    
    def __write(self, text, line):
        self.oled.text(text, line)

    def __clearAll(self):
        self.oled.clear()

    def __clear(self, line):
        self.oled.text("", line)

    def __setLayout(self, layout):
        self.oled.layout = layout
    
    def __show(self):
        self.oled.show()

    def updatePIR(self, data):
        self.lastDetection.acquire()
        self.lastTime.acquire()

        self.lastDetection.value =  data['detection']
        self.lastTime.value = data['timestamp']
        self.lastTime.release()
        self.lastDetection.release()

    def updateDHT22(self, data):
        self.lastTemperature.acquire()
        self.lastHumidity.acquire()
        self.lastTempUpdate.acquire()
        self.lastHumUpdate.acquire()

        self.lastTemperature.value = data['temperature']
        self.lastHumidity.value = data['humidity']
        self.lastTempUpdate.value = data['temperatureTimestamp']
        self.lastHumUpdate.value = data['humidityTimestamp']

        self.lastHumUpdate.release()
        self.lastTemperature.release()
        self.lastHumidity.release()
        self.lastTempUpdate.release()
 
    def updateSerial(self, data):
        self.lastPotentiometer.acquire()
        self.lastPotentiometerUpdate.acquire()

        self.lastPotentiometer.value = data['potentiometer']
        self.lastPotentiometerUpdate.value = data['timestamp']

        self.lastPotentiometerUpdate.release()
        self.lastPotentiometer.release()
           
    def start(self, DHT22Connection, PIRConnection, SerialConnection):
        self.displayProcess = Process(target=self.__updateDisplay, args=(DHT22Connection, PIRConnection, SerialConnection,))
        self.displayProcess.start()

    def stop(self):
        if self.displayProcess.is_alive():
            self.displayProcess.join()
        pass
            
    def __showDHT22(self):
        #set 3 lines layout for DHT22
        self.__setLayout(
            { 1: SmallLine(1, 1, font="FreeSans.ttf", size=14),
              2: SmallLine(1, 17, font="FreeSans.ttf", size=14),
              3: SmallLine(1, 33, font="FreeSans.ttf", size=14),
              4: SmallLine(1, 49, font="FreeSans.ttf", size=14)
            })

        self.lastTemperature.acquire()
        self.lastHumidity.acquire()
        self.lastTempUpdate.acquire()
        self.lastHumUpdate.acquire()

        if int(self.lastTempUpdate.value) == 0xdeadbeef or int(self.lastHumUpdate.value) == 0xdeadbeef: #check if data has been received
            self.lastHumUpdate.release()
            self.lastTempUpdate.release()
            self.lastHumidity.release()
            self.lastTemperature.release()
            return

        tempTime = time.localtime(self.lastTempUpdate.value)
        tempTime = time.strftime('%H:%M', tempTime)
        humTime  = time.localtime(self.lastHumUpdate.value)
        humTime  = time.strftime('%H:%M', humTime)

        self.__write(f'Temperature: {self.lastTemperature.value:.2f}', 1)
        self.__write(f'At time: {tempTime}',2)
        self.__write(f'Humidity: {self.lastHumidity.value:.2f}', 3)
        self.__write(f'At time: {humTime}', 4)
        self.__show()

        self.lastTemperature.release()
        self.lastHumidity.release()
        self.lastTempUpdate.release()
        self.lastHumUpdate.release()


    def __showPIR(self):
        #Set layout for PIR
        self.__setLayout(
            { 1: SmallLine(1, 2, font="FreeSans.ttf", size=14),
              2: SmallLine(1, 18, font="FreeSans.ttf", size=14)
            })

        self.lastDetection.acquire()
        self.lastTime.acquire()

        if int(self.lastTime.value) == 0xdeadbeef:               #check if data has been received
            self.lastTime.release()
            self.lastDetection.release()
            return

        readTime = time.localtime(self.lastTime.value)
        readTime = time.strftime('%H:%M', readTime)
        self.__write(f'Position: {self.lastDetection.value}', 1)
        self.__write(f'At time: {readTime}', 2)
        self.__show()

        self.lastTime.release()
        self.lastDetection.release()
         
    def __showSerial(self):
        #Set layout for serial
        self.__setLayout(
            { 1: SmallLine(1, 2, font="FreeSans.ttf", size=14),
              2: SmallLine(1, 18, font="FreeSans.ttf", size=14)
            })

        self.lastPotentiometer.acquire()
        self.lastPotentiometerUpdate.acquire()

        if int(self.lastPotentiometerUpdate.value) == 0xdeadbeef:                #check if data has been received
            self.lastPotentiometerUpdate.release()
            self.lastPotentiometer.release()
            return

        readTime = time.localtime(self.lastPotentiometerUpdate.value)
        readTime = time.strftime('%H:%M', readTime)
        self.__write(f'Potentiometer: {self.lastPotentiometer.value}', 1)
        self.__write(f'At time: {readTime}', 2)
        self.__show()
    
        self.lastPotentiometerUpdate.release()
        self.lastPotentiometer.release()

    def __updateDisplay(self, DHT22Connection, PIRConnection, SerialConnection):
        try:
            #get number of pages to show
            cycles = 0;
            if DHT22Connection:
                cycles = cycles + 1
            if PIRConnection:
                cycles = cycles + 1
            if SerialConnection:
                cycles = cycles + 1

            while True:
                try:
                    if DHT22Connection:
                        self.__showDHT22()
                        time.sleep(self.pageTime/ cycles)

                    if PIRConnection:
                        self.__showPIR()
                        time.sleep(self.pageTime / cycles)

                    if SerialConnection:
                        self.__showSerial()
                        time.sleep(self.pageTime / cycles)
                except OSError:
                    print("display disconnected", file=sys.stderr)
                    try:
                        self.oled = OledText(self.i2c, self.width, self.height)
                        time.sleep(1)
                    except Exception:
                        print("no display found", file=sys.stderr)
        except KeyboardInterrupt:
            sys.exit(0)

def main(argv):
    if len(argv) != 2:
        display = SSD1306_I2C()
        addressDHT22 = ('localhost',12345)
        passwordDHT22 = 'DHT22iscool'
        addressPIR = ('localhost',12346)
        passwordPIR = 'DHT22isbetter'
        addressSERIAL = ('localhost', 12347)
        passwordSERIAL = 'Serialiscool'
    else:
        display_dict = argv[1]
        updateTime = 1 / display_dict['FREQUENCY']
        display = SSD1306_I2C(pageTime = updateTime)
        addressDHT22 = (display_dict['DHT22_SERVER'], display_dict['DHT22_PORT'])
        passwordDHT22 = 'DHT22iscool'
        addressPIR = (display_dict['PIR_SERVER'], display_dict['PIR_PORT'])
        passwordPIR = 'DHT22isbetter'
        addressSERIAL = (display_dict['SERIAL_SERVER'], display_dict['SERIAL_PORT'])
        passwordSERIAL = 'Serialiscool'
    
    client = SensorClient(display)
    client.connectDHT22(addressDHT22, passwordDHT22)
    client.connectPIR(addressPIR, passwordPIR)
    client.connectSerial(addressSERIAL, passwordSERIAL)
    client.run()

if __name__ == "__main__":
    main(sys.argv)

