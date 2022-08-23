from datastoreGarbageCollector import mergingDataGarbageCollector
from pathlib import Path
from dataFrameGarbageCollector import garbageCollector
import time
import os
# import rankerConfig
import configparser

class dataGarbageCollector:
    def __init__(self):

        path = str(Path(os.path.dirname(os.path.abspath(__file__))))+"/rankerConfig.ini"
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.rankerConfig = self.config["settings"]
        workflow = self.rankerConfig["workflow"]
        serverless = mergingDataGarbageCollector()
        gc = garbageCollector(workflow)


if __name__ == "__main__":
    interuptTime = 60 * 60
    while True:
        start_time = time.time()
        x = dataGarbageCollector()
        print("--- %s seconds ---" % (time.time() - start_time))
        time.sleep(interuptTime)
