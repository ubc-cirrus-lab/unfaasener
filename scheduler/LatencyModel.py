import numpy as np
import configparser
from pathlib import Path
import os


class LatencyModel:
    def __init__(self):
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/latencyConfig.ini"
        )
        self.config = configparser.ConfigParser()
        self.config.read(path)
        self.latencyConfig = self.config["model"]

    def updateModel(self, mode, polynomialDegree, points):
        path = (
            str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/latencyConfig.ini"
        )
        x = []
        y = []
        for point in points:
            x.append(point[0])
            y.append(point[1])
        coefficients = np.polyfit(x, y, polynomialDegree)
        if mode == "vm":
            coefficientsStr = " ".join(str(c) for c in coefficients)
            self.latencyConfig["vmCoefficients"] = coefficientsStr
            with open(path, "w") as configfile:
                self.config.write(configfile)
        elif mode == "serverless":
            coefficientsStr = " ".join(str(c) for c in coefficients)
            self.latencyConfig["serverlessCoefficients"] = coefficientsStr
            with open(path, "w") as configfile:
                self.config.write(configfile)

    def getLinearAddedLatency(self, msgSize):
        vmCoefficients = self.latencyConfig["vmCoefficients"].split()
        serverlessCoefficients = self.latencyConfig["serverlessCoefficients"].split()
        baseLatencyVM = float(vmCoefficients[-1])
        baseLatencyServerless = float(serverlessCoefficients[-1])
        addedLatency = baseLatencyVM - baseLatencyServerless
        degree = len(vmCoefficients) - 1
        for i in range(degree):
            addedLatency += (msgSize ** (degree - i)) * (
                (float(vmCoefficients[i])) - (float(serverlessCoefficients[i]))
            )
        return addedLatency
        # return 0


if __name__ == "__main__":
    model = LatencyModel()
    model.updateModel("vm", 1, [(100, 40.9525), (100000, 51.8365)])
    model.updateModel("serverless", 1, [(100, 17.4505), (100000, 26.0175)])
    print(model.getLinearAddedLatency(1000000))
