from multiprocessing.connection import Listener
from multiprocessing import Process
import time
import sys
import json

class SensorServerClass:
    def __init__(self, address, password, sensor):
        self.address            = address
        self.password           = password
        self.clientProcess      = []
        self.sensor             = sensor
        self.serverProcess      = None

    def startServer(self):
        self.server = Listener(self.address, authkey=self.password.encode()) #Open server socket
        self.serverProcess = Process(target=self.__serverManager, args=())
        self.serverProcess.start()

    def __serverManager(self):
        while True:
            try:
                conn = self.server.accept()
                p = Process(target=self.__clientManager, args=(conn,))
                p.start()
                self.clientProcess.append(p)
            except KeyboardInterrupt:
                for p in self.clientProcess:
                    if p.is_alive():
                        p.join()
                self.server.close()
                sys.exit(0)

    def __clientManager(self, conn):
        while True:
            try:
                if not conn.closed:
                    data = self.sensor.getData()
                    if data != None:
                        conn.send(json.dumps(data))
                    time.sleep(0.5)
                else:
                    print('connection closed found!', file=sys.stderr)
            except ValueError:
                print('error while sending item', file=sys.stderr)
                conn.close()
                sys.exit(1)
            except ConnectionResetError:
                print('connection reset by client', file=sys.stderr)
                conn.close()
                sys.exit(2)
            except BrokenPipeError:
                print('client died!', file=sys.stderr)
                conn.close()
                sys.exit(3)
            except KeyboardInterrupt:
                conn.close()
                sys.exit(0)

    def start(self):
        self.sensor.startUpdater()
        self.startServer()

    def run(self):
        self.start()
        try:
            while True:
                time.sleep(10000)
        except KeyboardInterrupt:
            self.stop()
            sys.exit(0)

    def stop(self):
        if self.serverProcess.is_alive():
            self.serverProcess.join()
        self.sensor.stopUpdater()       

    #"with" keyword
    def __enter__(self):
        self.run()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
