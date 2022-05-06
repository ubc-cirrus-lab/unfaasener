
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1
from google.cloud import datastore
import datetime
import os
import json
import logging
import uuid
import base64
from sys import getsizeof
import Text2SpeechWorkflow
import ImageProcessing
import subprocess
from google.protobuf.json_format import MessageToJson
import docker
from google.cloud import functions_v1
import requests
import wget
import string
from zipfile import ZipFile
import subprocess
import sys


project_id = "ubc-serverless-ghazal"
subscription_id = "vmSubscriber1"

#publish_topic_id = "vm-subscribe"
#timeout = 22.0



subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)
DSclient = datastore.Client()
publisher = pubsub_v1.PublisherClient()
client = docker.from_env()

def containerize(functionname):
    # Create a client
    client = functions_v1.CloudFunctionsServiceClient()

    # Initialize request arguments
    request = functions_v1.GenerateDownloadUrlRequest(name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"+functionname,
    )

    # Make the request
    response = client.generate_download_url(request=request)
    downloadlink = str(response).split(' ')[1].split('"')[1]
    # Download the function
    print ("\nDownloading the function")
    wget.download(downloadlink,functionname+'.zip')
    request = functions_v1.GetFunctionRequest(
       name="projects/ubc-serverless-ghazal/locations/northamerica-northeast1/functions/"+functionname,
    )

    # Make the request
    response = client.get_function(request=request)
    entrypoint = response.entry_point

    # Unzip the function
    print ("\nUnzipping the function")
    with ZipFile(functionname+'.zip', 'r') as zipObj:
       zipObj.extractall(functionname)
    with open("/tmp/output.log", "a") as output:
       print ("\nCreating the Docker container \n")
       # Copy the Docker file to the unzipped folder
       subprocess.call("cp Dockerfile "+functionname, shell=True, stdout=output, stderr=output)
       subprocess.call("cp init.sh "+functionname, shell=True, stdout=output, stderr=output)
       file_object = open(functionname+'/main.py', 'a')
       file_object.write('import sys\n')
       file_object.write('def main():\n')
       file_object.write('    '+entrypoint+'(json.loads(sys.argv[1]),"dummy")\n')
       file_object.write("if __name__ == '__main__':\n")
       file_object.write('    main()\n')
       file_object.close()
       subprocess.call("cp Text2Speech/"+functionname + "/requirements.txt "+ functionname+"/requirements.txt" , shell=True, stdout=output, stderr=output)
       subprocess.call("cp ubc-serverless-ghazal-9bede7ba1a47.json "+functionname + "/ "  , shell=True, stdout=output, stderr=output)
       subprocess.call("sed -i 's/json.loads(base64.b64decode//g' "+functionname + "/main.py " , shell=True, stdout=output, stderr=output)
       subprocess.call('sed -i "s/.decode(\'utf-8\'))//g" ' + functionname + "/main.py " , shell=True, stdout=output, stderr=output)
       # Create the image from the Dockerfile also copy the function's code
       subprocess.call("cd "+functionname+"; docker build . < Dockerfile --tag name:"+functionname, shell=True, stdout=output, stderr=output)

def callback(message: pubsub_v1.subscriber.message.Message) -> None:
    global writtenData
    receivedDateObj = datetime.datetime.utcnow()
    decodedMessage = (json.loads(message.data.decode("utf-8"))).get("data")
    print(f"received data:{decodedMessage}")
    print(f"Received Date:{receivedDateObj}")
    msgID = message.attributes.get("identifier")
    routingData = message.attributes.get("routing")
    reqID = message.attributes.get("reqID")
    invokedFun = message.attributes.get("invokedFunction")
    notfound=1
    for image in client.images.list():
        if invokedFun in str(image.tags):
            print ("Image found")
            notfound=0
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
    print (str(jsonfile).replace('\'','"'))
    with open("/tmp/output.log", "a") as output:
        before  = datetime.datetime.now()
        #subprocess.call("docker run name:"+ invokedFun+" '"+  str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)
        #subprocess.call("docker run name:"+ invokedFun+" "+  str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)
        client.containers.run("name:"+ invokedFun,command="python3 /app/main.py '"+  str(jsonfile).replace('\'','"') + "' " + reqID )
        after  = datetime.datetime.now()
        delta =  after - before
        print ("Docker Execution Durations for "+invokedFun + " is " +str(delta.microseconds)+" microseconds")
def func1(msg):
    decodedMessage = json.loads(msg.decode("utf-8"))
    msg = decodedMessage["data"]["message"]
    print(f"function one invoked, received message: {msg}")
    print("First function was invoked in the VM")
def func2(msg):
    print(f"function2 invoked, received message: {msg}")
    print("Second function was invoked in the VM")

def branch2(msg):
    print(f"branch2 invoked, received message: {msg}")
    print("Second branch function was invoked in the VM")

def merged(msg):
    print(f"merged function invoked, received message: {msg}")
    print("Merged function was invoked in the VM")
def seqChained2(msg, start, ret):
    startTime = str(datetime.datetime.utcnow())
    decodedMessage = (json.loads(msg.decode("utf-8"))).get("data")
    n = int(decodedMessage.get("n"))+1
    startTimes = json.loads(start)
    startTimes.append(startTime)
    retTimes = json.loads(ret)
    retTimes.append(str(datetime.datetime.utcnow()))
    return n, startTimes, retTimes
def seqChained3(msg, start, ret):
    startTime = str(datetime.datetime.utcnow())
    decodedMessage = (json.loads(msg.decode("utf-8"))).get("data")
    n = int(decodedMessage.get("n"))+1
    startTimes = json.loads(start)
    startTimes.append(startTime)
    retTimes = json.loads(ret)
    retTimes.append(str(datetime.datetime.utcnow()))
    print(f"Final n : {n}")
    print(f"Start Times : {startTimes}")
    print(f"Return Times : {retTimes}")
writtenData = {}
with open('data.json', mode='w') as f:
    json.dump(writtenData, f)
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)
print(f"Listening for messages on {subscription_path}..\n")

with subscriber:
    try:
        streaming_pull_future.result()
    except Exception as e:
        print(f"Listening for messages on {subscription_path} threw an exception: {e.__class__}, {repr(e)}.")
        streaming_pull_future.cancel()
        streaming_pull_future.result()
