from multiprocessing import Process
import yaml
import sys
import time

#modules
import DHT22
import PIR
import SSD1306
import SerialDriver
import InfluxLoader

#dictionary of supported modules
modules = {
    'DHT22'     : DHT22.main,
    'PIR'       : PIR.main,
    'SSD1306'   : SSD1306.main,
    'SERIAL'    : SerialDriver.main,
    'INFLUX'    : InfluxLoader.main
}

processList = []
def main():
    try:
        #open configuration file
        with open("config.yaml", "r") as config:
            config_dict = yaml.safe_load(config)
            if config_dict == None:
                print('Configuration file empty', file=sys.stderr)
                sys.exit(1)
            #iterate objects on config file
            for k, val in config_dict.items():
                cmd = modules[k]
                print(f'starting {k}')
                p = Process(target=cmd, args=([k, val],))
                p.start()
                processList.append(p)
                time.sleep(1)
            while True:
                time.sleep(10000) #manager must wait children to stop
    except KeyboardInterrupt:
        for p in processList:
            if p.is_alive():
                p.join()
        sys.exit(0)
        
if __name__ == "__main__":
    main()
