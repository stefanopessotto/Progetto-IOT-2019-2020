from multiprocessing.connection import Client
from multiprocessing import Process
import time
import sys
import json

class SensorClient:
    def __init__(self, client):
        self.PIRConnection      = None
        self.DHT22Connection    = None
        self.SerialConnection   = None
        self.PIRJob             = None
        self.SerialJob          = None
        self.DHT22Job           = None
        self.client             = client

    def __manageClient(self, connection, updateCallback, closeCallback):
        while True:
            try: 
                if not connection.closed:
                    msg = connection.recv()
                    if msg == 'Adios':
                        closeCallback()
                        sys.exit(0)
                    data = json.loads(msg)
                    updateCallback(data)
            except EOFError:
                print('Closed socket found! Quitting', file=sys.stderr)
                closeCallback()
                sys.exit(2)
            except ConnectionResetError:
                print('Server died?', file=sys.stderr)
                closeCallback()
                sys.exit(3)
            except KeyboardInterrupt:
                closeCallback()
                sys.exit(0)
    
    def __closePIR(self):
        if not self.PIRConnection.closed:
            self.PIRConnection.close()
        self.PIRConnection = None

    def connectPIR(self, address, password):
        try:
            self.PIRConnection = Client(address, authkey=password.encode())
            self.PIRJob = Process(target=self.__manageClient, args=(self.PIRConnection, self.client.updatePIR, self.__closePIR))
            self.PIRJob.start()
        except ConnectionRefusedError:
            self.PIRConnection = None
            print('No PIR server found.. skipping!', file=sys.stderr)

    def __closeDHT22(self):
        if not self.DHT22Connection.closed:
            self.DHT22Connection.close()
        self.DHT22Connection = None

    def connectDHT22(self, address, password):
        try:
            self.DHT22Connection = Client(address, authkey=password.encode())
            self.DHT22Job = Process(target=self.__manageClient, args=(self.DHT22Connection, self.client.updateDHT22, self.__closeDHT22))
            self.DHT22Job.start()
        except ConnectionRefusedError:
            self.DHT22Connection = None
            print('No DHT22 server found.. skipping!', file=sys.stderr)

    def __closeSerial(self):
        if not self.SerialConnection.closed:
            self.SerialConnection.close()
        self.SerialConnection = None
    
    def connectSerial(self, address, password):
        try:
            self.SerialConnection = Client(address, authkey=password.encode())
            self.SerialJob = Process(target=self.__manageClient, args=(self.SerialConnection, self.client.updateSerial, self.__closeSerial))
            self.SerialJob.start()
        except ConnectionRefusedError:
            self.SerialConnection = None
            print('No serial server found.. skipping!', file=sys.stderr)

    def start(self):
        self.client.start((self.DHT22Connection != None), (self.PIRConnection != None), (self.SerialConnection != None))

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(10000)
        except KeyboardInterrupt:
            self.stop()
            sys.exit(0)

    def stop(self):
        if self.PIRJob != None and self.PIRJob.is_alive():
            self.PIRJob.join()
        if self.DHT22Job != None and self.DHT22Job.is_alive():
            self.DHT22Job.join()
        if self.SerialJob != None and self.SerialJob.is_alive():
            self.SerialJob.join()

        self.client.stop()
    #useful for with "with" keyword
    def __enter__(self):
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
