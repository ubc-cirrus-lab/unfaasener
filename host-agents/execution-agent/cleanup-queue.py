from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.cloud import datastore
import datetime
from pathlib import Path
import os
import json
import subprocess
import docker
from google.cloud import functions_v1
import wget
from zipfile import ZipFile
import subprocess
import sys
import configparser
from time import sleep
import docker
import sys
from datetime import timedelta

configPath = (
    str(Path(os.path.dirname(os.path.abspath(__file__))).resolve().parents[1])
    + "/project-config.ini"
)
globalConfig = configparser.ConfigParser()
globalConfig.read(configPath)
projectConfig = globalConfig["settings"]
project_id = str(projectConfig["projectid"])

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
                task["function"] = str(key2).replace("Number2", "")
                task["duration"] = executionDurations[key][key2]["duration"]
                task["start"] = executionDurations[key][key2]["start"]
                task["finish"] = executionDurations[key][key2]["finish"]
                task["host"] = executionDurations[key][key2]["host"]
                task["mergingPoint"] = executionDurations[key][key2]["mergingPoint"]
                datastore_client.put(task)
                # print ("###### Inserted one record in vmLogs")
            # executionDurations[key][key2] = {}
    #    executionDurations[key].pop(key2,None)
    # executionDurations.pop(key,None)
    # executionDurations = {}


def threaded_function(arg, lastexectimestamps):
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
                    all=True, filters={"ancestor": "name:" + key}
                )
                next(iter(cont)).stop()
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
        name="projects/"
        + project_id
        + "/locations/northamerica-northeast1/functions/"
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
        name="projects/"
        + project_id
        + "/locations/northamerica-northeast1/functions/"
        + functionname,
    )

    # Make the request
    response = client.generate_download_url(request=request)
    downloadlink = str(response).split(" ")[1].split('"')[1]
    # Download the function
    print("\nDownloading the function")
    wget.download(downloadlink, functionname + ".zip")
    request = functions_v1.GetFunctionRequest(
        name="projects/"
        + project_id
        + "/locations/northamerica-northeast1/functions/"
        + functionname,
    )

    # Make the request
    response = client.get_function(request=request)
    entrypoint = response.entry_point

    # Unzip the function
    print("\nUnzipping the function")
    with ZipFile(functionname + ".zip", "r") as zipObj:
        zipObj.extractall(functionname)
    with open("/tmp/output2.log", "a") as output:
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
            "cp vmExeModule.json " + functionname + "/ ",
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
    receivedDateObj = datetime.datetime.utcnow()
    decodedMessage = (json.loads(message.data.decode("utf-8"))).get("data")
    print(f"received data:{decodedMessage}")
    print(f"Received Date:{receivedDateObj}")
    msgID = message.attributes.get("identifier")
    routingData = message.attributes.get("routing")
    reqID = message.attributes.get("reqID")
    invokedFun = message.attributes.get("invokedFunction")
    notfound = 1
    message.ack()


# with open("data.json", mode="w") as f:
#     json.dump(writtenData, f)
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)


with subscriber:
    try:
        # num of seconds the subscriber pulls the unacked messages
        timeout = 15
        streaming_pull_future.result(timeout=timeout)
    except TimeoutError:
        streaming_pull_future.cancel()
        streaming_pull_future.result()
