from CreateGCFLogs import CreateGCFLogs
from AnalyzeLogs import AnalyzeLogs

num = int(input("Enter the number of messages to test: "))
interval = int(input("Enter byte difference between two consecutive messages: "))
testCount = int(input("Enter the test count per each message: "))
sleepTime = float(input("Enter the sleep time between calling functions in seconds"))
LargeMessages = int(
    input("Do you want to test large messages: (Enter 1 for yes and 0 for no)")
)
invoker = str(input("Do you want to invoke the function in vm or gcf?"))
function = str(
    input("If you select vm, please enter the function name, otherwise press enter")
)

creatingObj = CreateGCFLogs(
    num, interval, testCount, sleepTime, LargeMessages, invoker, function
)


logs = input("Enter the path to the logs file: ")
exeIDs = input("Enter the path to the publisher executionID file: ")
subscriber = input("Enter the Subscriber type: ")
vmData = input(
    "Enter the path to the subscriber's data file if you chose vm,otherwise press enter"
)

analyzingObj = AnalyzeLogs(logs, exeIDs, vmData, subscriber)
df = analyzingObj.parseLogs()
analyzingObj.createPlot(df)
analyzingObj.plotEachGp(df)
