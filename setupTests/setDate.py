import configparser
import sys
from pathlib import Path
import os

date = sys.argv[1]+ " " +sys.argv[2]
path = str(Path(os.path.dirname(os.path.abspath(__file__))))+"/dateTest.ini"
config = configparser.ConfigParser()
config.read(path)
rankerConfig = config["settings"]
rankerConfig["date"] = date
# str(datetime.datetime.now())
with open(path, "w") as configfile:
    config.write(configfile)
