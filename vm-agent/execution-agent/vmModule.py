from concurrent.futures import TimeoutError
import copy
import datetime
from datetime import timedelta
import docker
from google.cloud import datastore, functions_v1, pubsub_v1
from google.cloud.pubsub_v1.subscriber import exceptions as sub_exceptions
import json
import configparser
from multiprocessing import cpu_count
import os
from pathlib import Path
import psutil
import subprocess
import sys
from threading import Thread, Lock
from time import sleep
import uuid
import wget
from zipfile import ZipFile
import shlex


path = (
            str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
            + "/scheduler/rankerConfig.ini"
        )
config = configparser.ConfigParser()
config.read(path)
rankerConfig =config["settings"]
muFactor =rankerConfig["muFactor"]

project_id = "ubc-serverless-ghazal"
subscription_id = sys.argv[1]
# timeout = 22.0
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/vmExeModule.json"
)


subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)
datastore_client = datastore.Client()
publisher = pubsub_v1.PublisherClient()
client = docker.from_env()
# reqQueue = []
executionDurations = {}
cacheDurations = {}
memoryLimits = {}
lastexecutiontimestamps = {}
client_api = docker.APIClient(base_url="unix://var/run/docker.sock")
info = client_api.df()

# concurrency configs and locking variables
CONCURRENCY_LIMIT = int((os.cpu_count())/float(muFactor))
msgQueue = []  # queue of msgIDs used to enforce execution order
activeThreads = []
activeThreadCheckLock = Lock()
contExecRunLock = Lock()
activeContainerSearchList = {}  # function -> list of container
contsPerFunct = {}

def flushExecutionDurations():
    global executionDurations
    global cacheDurations

    cachePath = (
        str(Path(os.path.dirname(os.path.abspath(__file__))))
        + "/data/cachedVMData.json"
    )
    if os.path.isfile(cachePath):
        with open(cachePath, "r", os.O_NONBLOCK) as json_file:
            cach_json = json.load(json_file)
            newCachJSon = {
                key: cach_json.get(key, []) + cacheDurations.get(key, [])
                for key in set(list(cach_json.keys()) + list(cacheDurations.keys()))
            }
            cacheDurations = {}
    else:
        newCachJSon = cacheDurations
        cacheDurations = {}
    with open(cachePath, "w", os.O_NONBLOCK) as f:
        json.dump(newCachJSon, f)
    tempexecutionDurations = copy.deepcopy(executionDurations)
    kind = "vmLogs"
    for key in tempexecutionDurations.keys():
        if len(tempexecutionDurations[key]) == 7:
            newHash = uuid.uuid4().hex
            task_key = datastore_client.key(kind, str(key) + str(newHash))
            task = datastore.Entity(key=task_key)
            task["reqID"] = tempexecutionDurations[key]["reqID"]
            removedPart = str(key).replace(
                str(tempexecutionDurations[key]["mergingPoint"]), ""
            )
            task["function"] = str(removedPart).replace(str(task["reqID"]), "")
            task["duration"] = tempexecutionDurations[key]["duration"]
            task["start"] = tempexecutionDurations[key]["start"]
            task["finish"] = tempexecutionDurations[key]["finish"]
            task["host"] = tempexecutionDurations[key]["host"]
            if ":fanout:" in tempexecutionDurations[key]["mergingPoint"]:
                tempexecutionDurations[key]["mergingPoint"] = ""
            task["mergingPoint"] = tempexecutionDurations[key]["mergingPoint"]
            datastore_client.put(task)
            executionDurations.pop(key)


def threaded_function(arg, lastexectimestamps):
    global executionDurations
    global activeThreadCheckLock
    global activeThreads
    while True:
        staticlastexectimestamps = lastexectimestamps
        for key in list(staticlastexectimestamps):
            if (
                lastexectimestamps[key] + timedelta(seconds=600)
            ) < datetime.datetime.now():
                cont = client.containers.list(
                    # all=True, filters={"ancestor": "name:" + key}
                    all=True,
                    filters={"id": key},
                )
                for container_single in cont:
                    container_single.stop(timeout=2)
                # print("Stopped Old Container " + key)
        # staticexecutionDurations = executionDurations
        if executionDurations != {}:
            # try:
            flushExecutionDurations()
            # except:
            #     print("Error in flushing the vmLogs")

        # cleaning dead threads from the queue
        activeThreadCheckLock.acquire()
        for thread in activeThreads:
            if thread.is_alive() is False:
                activeThreads.remove(thread)
        activeThreadCheckLock.release()
        
        # sleep
        sleep(2)



def getFunctionParameters(functionname):
    client = functions_v1.CloudFunctionsServiceClient()
    request = functions_v1.GetFunctionRequest(
        name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"
        + functionname,
    )
    # print(
    #     "Function Parameters"
    #     + str(client.get_function(request=request).available_memory_mb)
    # )
    memoryLimits[functionname] = (
        str(client.get_function(request=request).available_memory_mb) + "m"
    )



def containerize(functionname):
    # Create a client
    client = functions_v1.CloudFunctionsServiceClient()

    # Initialize request arguments
    request = functions_v1.GenerateDownloadUrlRequest(
        name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"
        + functionname,
    )

    # Make the request
    response = client.generate_download_url(request=request)
    downloadlink = str(response).split(" ")[1].split('"')[1]

    # Download the function
    # print("\nDownloading the function")
    wget.download(downloadlink, functionname + ".zip")
    request = functions_v1.GetFunctionRequest(
        name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"
        + functionname,
    )

    # Make the request
    response = client.get_function(request=request)
    entrypoint = response.entry_point

    # Unzip the function
    # print("\nUnzipping the function")
    with ZipFile(str(Path(os.path.dirname(os.path.abspath(__file__))))+"/"+functionname + ".zip", "r") as zipObj:
        zipObj.extractall(functionname)
    with open(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/output2.log", "a"
    ) as output:
        # print("\nCreating the Docker container \n")
        # Copy the Docker file to the unzipped folder
        subprocess.call(
            "cp "+str(Path(os.path.dirname(os.path.abspath(__file__))))+"/Dockerfile "+str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+ functionname, shell=True, stdout=output, stderr=output
        )
        subprocess.call(
            "cp "+str(Path(os.path.dirname(os.path.abspath(__file__))))+"/init.sh " +str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+functionname, shell=True, stdout=output, stderr=output
        )
        file_object = open(str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+functionname + "/main.py", "a")
        file_object.write("import sys\n")
        file_object.write("def main():\n")
        file_object.write("    " + entrypoint + '(json.loads(sys.argv[1]),"dummy")\n')
        file_object.write(
            "    " + entrypoint + "(json.loads(sys.argv[1]),sys.argv[2])\n"
        )

        file_object.write("if __name__ == '__main__':\n")
        file_object.write("    main()\n")
        file_object.close()
        subprocess.call(
            "cp "+str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/ubc-serverless-ghazal-9bede7ba1a47.json " + str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+ functionname + "/ ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call(
            "sed -i 's/json.loads(base64.b64decode//g' " +str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+ functionname + "/main.py ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call(
            "sed -i \"s/.decode('utf-8'))//g\" " +str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+ functionname + "/main.py ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        # Create the image from the Dockerfile also copy the function's code
        subprocess.call(
            "cd "
            +str(Path(os.path.dirname(os.path.abspath(__file__))))
            +"/"
            + functionname
            + "; docker build . < Dockerfile --tag name:"
            + functionname,
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call("ls",stdout=output)
        subprocess.run("rm -rf "+str(Path(os.path.dirname(os.path.abspath(__file__)))) +"/"+ functionname+"*",shell=True)








def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    before = datetime.datetime.now()
    global activeThreads
    global activeThreadCheckLock
    receivedDateObj = datetime.datetime.utcnow()
    decodedMessage = (json.loads(message.data.decode("utf-8"))).get("data")
    print(f"received data:{decodedMessage}")
    print(f"Received Date:{receivedDateObj}")
    ack_future = message.ack_with_response()  # block to prevent race condition
    try:
        # Block on result of acknowledge call.
        # When `timeout` is not set, result() will block indefinitely,
        # unless an exception is encountered first.
        ack_future.result(timeout=10)
        print(f"Ack for message {message.message_id} successful.")
    except sub_exceptions.AcknowledgeError as e:
        print(f"Ack for message {message.message_id} failed with error: {e.error_code}")
    ## We want something like '{"data": {"message": "testing"}}'
    jsonfile = {
        "data": json.loads(message.data.decode("utf-8")),
        "attributes": message.attributes,
    }
    checkedForAvailableThread = False
    while len(activeThreads) >= CONCURRENCY_LIMIT:
        if((((datetime.datetime.now())- before).total_seconds()) * 1000 > 1000):
            invokedFun = jsonfile["attributes"].get("invokedFunction")
            reqID = jsonfile["attributes"].get("reqID")
            jsonfile["attributes"]["routing"] = (jsonfile["attributes"].get("routing")).replace("A", "0")
            jsonfile["attributes"] = dict(jsonfile["attributes"])
            topic_path = publisher.topic_path(project_id, invokedFun)
            publish_future = publisher.publish(topic_path, data=(json.dumps(jsonfile["data"])).encode('utf-8'), **jsonfile["attributes"])
            publish_future.result()
            print("While waiting for threads, Request of function: ", invokedFun, " with reqID: ", reqID, " has forwarded to the serverless equivalent!")
            return
        threadsRemoved = False
        checkedForAvailableThread = True
        activeThreadCheckLock.acquire()
        for thread in activeThreads:
            if thread.is_alive() is False:
                activeThreads.remove(thread)
                threadsRemoved = True
                print("garbage collected the dead thread")
                break
        print("active request processing threads: " + str(len(activeThreads)))
        if threadsRemoved:
            thread2 = Thread(target=processReqs, args=(jsonfile, before))
            activeThreads.append(thread2)
            thread2.start()
            activeThreadCheckLock.release()
            break
        activeThreadCheckLock.release()
        sleep(0.02)

    if checkedForAvailableThread is False:
        thread2 = Thread(target=processReqs, args=(jsonfile, before))
        activeThreads.append(thread2)
        thread2.start()


def processReqs(jsonfile, before):
    tot_cont_hash = uuid.uuid4().hex
    global executionDurations
    global cacheDurations
    global cpulimit
    global msgQueue
    global activeContainerSearchList
    global contExecRunLock
    global contsPerFunct
    msgID = jsonfile["attributes"].get("identifier")
    reqID = jsonfile["attributes"].get("reqID")
    invokedFun = jsonfile["attributes"].get("invokedFunction")
    tmpInvokedFun = jsonfile["attributes"].get("invokedFunction")
    # TODO: try/except error handling


    cpuutil = psutil.cpu_percent()
    locked = False
    if cpuutil > 80:
        msgQueue.append(msgID)
        locked = True
    while locked:
        cpuutil = psutil.cpu_percent()
        if (cpuutil < 80) and (msgQueue.index(msgID) < 3):
            msgQueue.remove(msgID)
            break
        elif((((datetime.datetime.now())- before).total_seconds()) * 1000 > 2000):
            jsonfile["attributes"]["routing"] = (jsonfile["attributes"].get("routing")).replace("A", "0")
            jsonfile["attributes"] = dict(jsonfile["attributes"])
            topic_path = publisher.topic_path(project_id, invokedFun)
            publish_future = publisher.publish(topic_path, data=(json.dumps(jsonfile["data"])).encode('utf-8'), **jsonfile["attributes"])
            publish_future.result()
            msgQueue.remove(msgID)
            print("Waiting for CPU, Request of function: ", invokedFun, " with reqID: ", reqID, " has forwarded to the serverless equivalent!")
            return
        print(
            "CPU is " + str(cpuutil) + " and queue length is " + str(len(msgQueue))
        )
        sleep(0.01)

    try:
        subprocess.check_output(shlex.split(("docker image inspect name:"+ invokedFun))).decode('utf-8')
    except subprocess.CalledProcessError:
        containerize(invokedFun)
    # This part allows reuse of existing containers , but impacts the usability of the system at high RequestPerSecond
    # It is disabled to enable the system to create more containers as more requests arrive
    # These containers are then stopped by the thread
    # TO -renable it , just remove the line what sets conts = {}
    # conts = {} #THis line can be removed to allow reusing containers
    execution_complete = 0
    localcontsPerFunct = contsPerFunct.copy()
    if tmpInvokedFun in localcontsPerFunct.keys():
        conts = localcontsPerFunct[tmpInvokedFun]
    else:
        conts = client.containers.list(
            all=True, filters={"ancestor": "name:" + invokedFun}
        )
        contExecRunLock.acquire()
        contsPerFunct[tmpInvokedFun] = conts
        contExecRunLock.release()
    if len(conts) != 0:
        for cont in conts:
            contExecRunLock.acquire()
            if tmpInvokedFun in activeContainerSearchList.keys():
                if cont not in activeContainerSearchList[tmpInvokedFun]:
                    activeContainerSearchList[tmpInvokedFun].append(cont)
                    contExecRunLock.release()
                else:
                    contExecRunLock.release()
                    continue
            else:
                activeContainerSearchList[tmpInvokedFun] = [cont]
                contExecRunLock.release()
            if (cont.attrs['State']['Running']):
                if len(cont.top()["Processes"]) > 1:
                    contExecRunLock.acquire()
                    activeContainerSearchList[tmpInvokedFun].remove(cont)
                    contExecRunLock.release()
                    continue
            else:
                cont.start()
            cont.exec_run(
                "python3 /app/main.py '"
                + str(jsonfile).replace("'", '"')
                + "' "
                + reqID,
                detach=False,
            )
            after = datetime.datetime.now()
            lastexecutiontimestamps[invokedFun] = before
            execution_complete = 1
            contExecRunLock.acquire()
            activeContainerSearchList[tmpInvokedFun].remove(cont)
            contExecRunLock.release()
            print(f"{tot_cont_hash}:Total exe time::: {(((datetime.datetime.now()) - before).total_seconds())} seconds.{reqID}")
            break

    if execution_complete == 0:
        if invokedFun not in memoryLimits:
            getFunctionParameters(invokedFun)
        container = client.containers.create(
            "name:" + invokedFun,
            mem_limit=str(memoryLimits[invokedFun]),
            cpu_period=100000,
            cpu_quota=100000,
            command="tail -f /etc/hosts",
            detach=False,
            user="bin",
        )
        lastexecutiontimestamps[container.id] = before
        container.start()
        cmd = (
            "python3 /app/main.py '"
            + str(jsonfile).replace("'", '"')
            + "' "
            + reqID
        )
        container.exec_run(cmd, detach=False)
        print(f"{tot_cont_hash}:Exe time after creation::: {(((datetime.datetime.now()) - before).total_seconds())} seconds.{reqID}")
        after = datetime.datetime.now()
        contExecRunLock.acquire()
        contsPerFunct[tmpInvokedFun].append(container)
        contExecRunLock.release()

    delta = after - before
    if jsonfile["attributes"].get("branch") != None:
        # Cover the Merging functions
        invokedFun = (
            str(invokedFun) + str(jsonfile["attributes"].get("branch")) + str(reqID)
        )
        executionDurations[invokedFun] = {}

    if (invokedFun + str(reqID)) in executionDurations.keys():
        newHash = uuid.uuid4().hex
        invokedFun = str(invokedFun) + ":fanout:" + str(newHash) + str(reqID)
        executionDurations[invokedFun] = {}
    else:
        invokedFun = invokedFun + str(reqID)
        executionDurations[invokedFun] = {}

    executionDurations[invokedFun]["duration"] = str(
        ((delta).total_seconds()) * 1000
    )
    if tmpInvokedFun not in cacheDurations.keys():
        cacheDurations[tmpInvokedFun] = []
        cacheDurations[tmpInvokedFun].append(
            float(((delta).total_seconds()) * 1000)
        )
    else:
        cacheDurations[tmpInvokedFun].append(
            float(((delta).total_seconds()) * 1000)
        )
    executionDurations[invokedFun]["reqID"] = reqID
    executionDurations[invokedFun]["start"] = str(before)
    executionDurations[invokedFun]["finish"] = str(after)
    executionDurations[invokedFun]["host"] = sys.argv[2]
    executionDurations[invokedFun]["function"] = str(invokedFun)
    executionDurations[invokedFun]["mergingPoint"] = ""
    if jsonfile["attributes"].get("branch") != None:
        executionDurations[invokedFun]["mergingPoint"] = str(
            jsonfile["attributes"].get("branch")
        )
    elif ":fanout:" in invokedFun:
        executionDurations[invokedFun]["mergingPoint"] = ":fanout:" + str(newHash)


flow_control = pubsub_v1.types.FlowControl(max_messages=20)
streaming_pull_future = subscriber.subscribe(
    subscription_path, callback=callback, flow_control=flow_control
)
print(f"Listening for messages on {subscription_path}..\n")
thread = Thread(target=threaded_function, args=(1000000, lastexecutiontimestamps))
thread.start()


with subscriber:
    try:
        streaming_pull_future.result()
    except Exception as e:
        print(
            f"Listening for messages on {subscription_path} threw an exception: {e.__class__}, {repr(e)}."
        )
        streaming_pull_future.cancel()
        streaming_pull_future.result()
