from multiprocessing import Process, Queue
from influxdb import InfluxDBClient
from SensorClient import SensorClient
from collections import defaultdict
import time
import sys
import ctypes
import json
#import requests  #used to remove warning when SSL is used

class InfluxLoader:
    
    def __init__(self, address, port, user, password, database):
#        requests.packages.urllib3.disable_warnings() # disable ssl verification warning (https://github.com/influxdata/influxdb-python/issues/240)
        self.address        = address
        self.port           = port
        self.database       = database
        self.user           = user
        self.password       = password
        self.client         = None
        self.client         = InfluxDBClient(self.address, self.port, username=self.user, password=self.password, database=self.database)#, ssl=True, verify_ssl=False)
        self.sharedQueue    = Queue()
        self.uploadProcess  = None
    
    def __write(self, data):
        self.client.write_points(data)

    def start(self, DHT22Connection, PIRConnection, SerialConnection):
        self.uploadProcess = Process(target=self.__uploadData, args=())
        self.uploadProcess.start()

    def stop(self):
        self.client.close()
        self.client = None
        if self.uploadProcess.is_alive():
            self.uploadProcess.join()
        self.uploadProcess = None

    def __uploadData(self):
        try:
            while True:
                toUpload = []
                #move data from shared queue to list
                while not self.sharedQueue.empty():
                    toUpload.append(self.sharedQueue.get())
                #write list on database
                if len(toUpload) > 0:
                    self.__write(toUpload)
                time.sleep(5)
        except KeyboardInterrupt:
            if len(toUpload) > 0:
                self.__write(toUpload) #finish to upload remaining data
            sys.exit(0) 
    def updatePIR(self, data):
        measure = {}
        measure['measurement'] = 'PIR'
        #fix time problem: convert to utc
        measure['time'] = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(data['timestamp']))
        measure['fields'] = {'position': data['detection']}
        measure['tags'] = {'host': 'py', 'sensor': 'PIR00'}
        self.sharedQueue.put(measure)
         
    def updateDHT22(self, data):
        measure = {}
        measure['measurement'] = 'DHT22'
        measure['tags'] = {'host': 'py', 'sensor': 'DHT22_00'}
        measure['fields'] = {'temperature': data['temperature'], 'humidity': data['humidity']}
        #fix time problem: convert to utc
        measure['time'] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(data['temperatureTimestamp']))
        self.sharedQueue.put(measure)

    def updateSerial(self, data):
        measure = {}
        measure['measurement'] = 'Serial'
        measure['tags'] = {'host': 'py', 'channel': 'Serial00'}
        measure['fields'] = {'potentiometer': data['potentiometer']}
        #fix time problem: convert to utc
        measure['time'] = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime(data['timestamp']))
        self.sharedQueue.put(measure)
           
def main(argv):
    if len(argv) != 2:
        dbDriver = InfluxLoader("localhost", 8086, 'sensors', None, None)
        addressDHT22 = ('localhost',12345)
        passwordDHT22 = 'DHT22iscool'
        addressPIR = ('localhost',12346)
        passwordPIR = 'DHT22isbetter'
        addressSERIAL = ('localhost', 12347)
        passwordSERIAL = 'Serialiscool'
    else:
        db_dict = argv[1]
        db_dict = defaultdict(str, db_dict)
        dbDriver = InfluxLoader(db_dict['HOST'], db_dict['PORT'], db_dict['USER'], db_dict['PASSWORD'], db_dict['DATABASE'])
        addressDHT22 = (db_dict['DHT22_SERVER'], db_dict['DHT22_PORT'])
        passwordDHT22 = 'DHT22iscool'
        addressPIR = (db_dict['PIR_SERVER'], db_dict['PIR_PORT'])
        passwordPIR = 'DHT22isbetter'
        addressSERIAL = (db_dict['SERIAL_SERVER'], db_dict['SERIAL_PORT'])
        passwordSERIAL = 'Serialiscool'

    client = SensorClient(dbDriver)
    client.connectDHT22(addressDHT22, passwordDHT22)
    client.connectPIR(addressPIR, passwordPIR)
    client.connectSerial(addressSERIAL, passwordSERIAL)
    client.run()

if __name__ == "__main__":
    main(sys.argv)

