from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.cloud import datastore
import datetime
from pathlib import Path
import os
import json
import uuid
import subprocess
import docker
from google.cloud import functions_v1
import wget
from zipfile import ZipFile
import subprocess
import sys
import uuid
from threading import Thread
from time import sleep
import docker
import sys
from datetime import timedelta
from multiprocessing import cpu_count


project_id = "ubc-serverless-ghazal"
# subscription_id = "vmSubscriber1"
subscription_id = sys.argv[1]

# publish_topic_id = "vm-subscribe"
# timeout = 22.0
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/vmExeModule.json"
)


subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)
datastore_client = datastore.Client()
publisher = pubsub_v1.PublisherClient()
client = docker.from_env()
writtenData = {}
executionDurations = {}
memoryLimits = {}
cpuLimits = {}
lastexecutiontimestamps = {}
client_api = docker.APIClient(base_url="unix://var/run/docker.sock")
info = client_api.df()


def flushExecutionDurations(executionDurations):
    seed = 0
    kind = "vmLogs"
    for key in list(executionDurations):
        for key2 in list(executionDurations[key]):
            if executionDurations[key][key2] != {}:
                task_key = datastore_client.key(kind, str(key) + str(seed))
                task = datastore.Entity(key=task_key)
                seed = seed + 1
                task["reqID"] = key
                task["function"] = str(key2).replace(
                    executionDurations[key][key2]["mergingPoint"], ""
                )
                task["duration"] = executionDurations[key][key2]["duration"]
                task["start"] = executionDurations[key][key2]["start"]
                task["finish"] = executionDurations[key][key2]["finish"]
                task["host"] = executionDurations[key][key2]["host"]
                if ":fanout:" in executionDurations[key][key2]["mergingPoint"]:
                    executionDurations[key][key2]["mergingPoint"] = ""
                task["mergingPoint"] = executionDurations[key][key2]["mergingPoint"]
                datastore_client.put(task)
                # print ("###### Inserted one record in vmLogs")
            # executionDurations[key][key2] = {}
    #    executionDurations[key].pop(key2,None)
    # executionDurations.pop(key,None)
    # executionDurations = {}


def threaded_function(arg, lastexectimestamps):
    global executionDurations
    while True:
        print("running")
        staticlastexectimestamps = lastexectimestamps
        for key in list(staticlastexectimestamps):
            print(key)
            print(lastexectimestamps[key])
            if (
                lastexectimestamps[key] + timedelta(seconds=5)
            ) < datetime.datetime.now():
                cont = client.containers.list(
                    #all=True, filters={"ancestor": "name:" + key}
                    all=True, filters={"id": key}
                )
                for container_single in cont:
                    container_single.stop(timeout=5)
                print("Stopped Old Container " + key)
        staticexecutionDurations = executionDurations
        if staticexecutionDurations != {}:
            try:
                flushExecutionDurations(staticexecutionDurations)
            except:
                print("Error in flushing the vmLogs")

        # wait 1 sec in between each thread
        sleep(1)


def getFunctionParameters(functionname):
    client = functions_v1.CloudFunctionsServiceClient()
    request = functions_v1.GetFunctionRequest(
        name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"
        + functionname,
    )
    print(
        "Function Parameters"
        + str(client.get_function(request=request).available_memory_mb)
    )
    memoryLimits[functionname] = (
        str(client.get_function(request=request).available_memory_mb) + "MB"
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
    print("\nDownloading the function")
    wget.download(downloadlink, functionname + ".zip")
    request = functions_v1.GetFunctionRequest(
        name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"
        + functionname,
    )

    # Make the request
    response = client.get_function(request=request)
    entrypoint = response.entry_point

    # Unzip the function
    print("\nUnzipping the function")
    with ZipFile(functionname + ".zip", "r") as zipObj:
        zipObj.extractall(functionname)
    with open(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/output2.log", "a"
    ) as output:
        print("\nCreating the Docker container \n")
        # Copy the Docker file to the unzipped folder
        subprocess.call(
            "cp Dockerfile " + functionname, shell=True, stdout=output, stderr=output
        )
        subprocess.call(
            "cp init.sh " + functionname, shell=True, stdout=output, stderr=output
        )
        file_object = open(functionname + "/main.py", "a")
        file_object.write("import sys\n")
        file_object.write("def main():\n")
        file_object.write("    " + entrypoint + '(json.loads(sys.argv[1]),"dummy")\n')
        file_object.write("if __name__ == '__main__':\n")
        file_object.write("    main()\n")
        file_object.close()
        subprocess.call(
            "cp Text2Speech/"
            + functionname
            + "/requirements.txt "
            + functionname
            + "/requirements.txt",
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call(
            "cp ubc-serverless-ghazal-9bede7ba1a47.json " + functionname + "/ ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call(
            "sed -i 's/json.loads(base64.b64decode//g' " + functionname + "/main.py ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        subprocess.call(
            "sed -i \"s/.decode('utf-8'))//g\" " + functionname + "/main.py ",
            shell=True,
            stdout=output,
            stderr=output,
        )
        # Create the image from the Dockerfile also copy the function's code
        subprocess.call(
            "cd "
            + functionname
            + "; docker build . < Dockerfile --tag name:"
            + functionname,
            shell=True,
            stdout=output,
            stderr=output,
        )


def callback(message: pubsub_v1.subscriber.message.Message) -> None:

    global writtenData
    global executionDurations
    global cpulimit
    # Initalize cpuLimits
    n_cores = cpu_count()
    cpuLimits['128MB'] = 83000 
    cpuLimits['256MB'] = 167000 
    cpuLimits['512MB'] = 333000 
    cpuLimits['1024MB'] = 583000 
    cpuLimits['2048MB'] = 1000000 
    cpuLimits['4096MB'] = 2000000 
    cpuLimits['8192MB'] = 2000000 
    cpuLimits['16384MB'] = 4000000 

    receivedDateObj = datetime.datetime.utcnow()
    decodedMessage = (json.loads(message.data.decode("utf-8"))).get("data")
    print(f"received data:{decodedMessage}")
    print(f"Received Date:{receivedDateObj}")
    msgID = message.attributes.get("identifier")
    routingData = message.attributes.get("routing")
    reqID = message.attributes.get("reqID")
    invokedFun = message.attributes.get("invokedFunction")
    notfound = 1
    for image in client.images.list():
        if invokedFun in str(image.tags):
            print("Image found")
            notfound = 0
    if notfound == 1:
        containerize(invokedFun)
    writtenData[msgID] = {}
    writtenData[msgID]["receivedDate"] = str(receivedDateObj)
    if message.attributes:
        print("Attributes:")
        for key in message.attributes:
            value = message.attributes.get(key)
            print(f"{key}: {value}")
            (writtenData[msgID])[key] = value
    message.ack()
    ## We want something like '{"data": {"message": "testing"}}'
    jsonfile = {
        "data": json.loads(message.data.decode("utf-8")),
        "attributes": message.attributes,
    }
    print(str(jsonfile).replace("'", '"'))
    if invokedFun not in memoryLimits:
        getFunctionParameters(invokedFun)
    if reqID not in executionDurations:
        executionDurations[reqID] = {}
    if invokedFun not in executionDurations[reqID]:
        executionDurations[reqID][invokedFun] = {}

    with open(
        str(Path(os.path.dirname(os.path.abspath(__file__)))) + "/output2.log", "a"
    ) as output:
        before = datetime.datetime.now()
        conts = client.containers.list(
            all=True, filters={"ancestor": "name:" + invokedFun}
        )
        print(len(conts))
        #This part allows reuse of existing containers , but impacts the usability of the system at high RequestPerSecond
        #It is disabled to enable the system to create more containers as more requests arrive
        #These containers are then stopped by the thread
        # TO -renable it , just remove the line what sets conts = {}
        conts = {} #THis line can be removed to allow reusing containers
        if len(conts) != 0:
            cont = next(iter(conts))
            cont.start()
            cont.exec_run(
                "python3 /app/main.py '"
                + str(jsonfile).replace("'", '"')
                + "' "
                + reqID,
                detach=False,
            )
            lastexecutiontimestamps[invokedFun] = before
            print(lastexecutiontimestamps)
        else:
            container = client.containers.create(
                "name:" + invokedFun,
                mem_limit=str(memoryLimits[invokedFun]),
                cpu_period=1000000,
                cpu_quota=int(cpuLimits[str(memoryLimits[invokedFun])]),
                command="tail -f /etc/hosts",
                detach=False,
            )
            #lastexecutiontimestamps[invokedFun] = before
            lastexecutiontimestamps[container.id] = before
            container.start()
            cmd = (
                "python3 /app/main.py '"
                + str(jsonfile).replace("'", '"')
                + "' "
                + reqID
            )
            print(cmd)
            container.exec_run(cmd, detach=False)

        after = datetime.datetime.now()
        delta = after - before
        if executionDurations[reqID][invokedFun] != {}:
            if message.attributes.get("branch") != None:
                # Cover the second Merging function
                invokedFun = (
                    str(invokedFun) + str(message.attributes.get("branch"))
                )
                executionDurations[reqID][invokedFun] = {}
            else:
                newHash = uuid.uuid4().hex
                invokedFun = str(invokedFun) + ":fanout:" + str(newHash)
                executionDurations[reqID][invokedFun] = {}

        executionDurations[reqID][invokedFun]["duration"] = str(
            delta.microseconds / 1000
        )
        executionDurations[reqID][invokedFun]["start"] = str(before)
        executionDurations[reqID][invokedFun]["finish"] = str(after)
        executionDurations[reqID][invokedFun]["host"] = sys.argv[2]
        executionDurations[reqID][invokedFun]["function"] = str(invokedFun)
        executionDurations[reqID][invokedFun]["mergingPoint"] = ""
        if message.attributes.get("branch") != None:
            executionDurations[reqID][invokedFun]["mergingPoint"] = str(
                message.attributes.get("branch")
            )
        elif ":fanout:" in invokedFun:
            executionDurations[reqID][invokedFun]["mergingPoint"] = ":fanout:" + str(newHash)


with open("data.json", mode="w") as f:
    json.dump(writtenData, f)
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")
thread = Thread(target=threaded_function, args=(1000000, lastexecutiontimestamps))
thread.start()
# thread.join()


with subscriber:
    try:
        streaming_pull_future.result()
    except Exception as e:
        print(
            f"Listening for messages on {subscription_path} threw an exception: {e.__class__}, {repr(e)}."
        )
        streaming_pull_future.cancel()
        streaming_pull_future.result()
