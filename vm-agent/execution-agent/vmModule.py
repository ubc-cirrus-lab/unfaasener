
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
project_id = "ubc-serverless-ghazal"
subscription_id = "vmSubscriber1"
#publish_topic_id = "vm-subscribe"
#timeout = 22.0



subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(project_id, subscription_id)
DSclient = datastore.Client()
publisher = pubsub_v1.PublisherClient()

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

    if invokedFun == "Text2SpeechCensoringWorkflow_Text2Speech":
        print (str(jsonfile).replace('\'','"'))
        #filename = Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Text2Speech(decodedMessage.get("message"), reqID)
        with open("/tmp/output.log", "a") as output:
            subprocess.call("docker run name:Text2SpeechCensoringWorkflow_Text2Speech "+  str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)
    if invokedFun == "Text2SpeechCensoringWorkflow_Conversion":
        print (str(jsonfile).replace('\'','"'))
        with open("/tmp/output.log", "a") as output:
            subprocess.call("docker run name:Text2SpeechCensoringWorkflow_Conversion "+  str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)
    if invokedFun == "Text2SpeechCensoringWorkflow_Profanity":
        print (str(jsonfile).replace('\'','"'))
        with open("/tmp/output.log", "a") as output:
            subprocess.call("docker run name:Text2SpeechCensoringWorkflow_Profanity '"+ str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)

    if invokedFun == "Text2SpeechCensoringWorkflow_MergingPoint":
        print (str(jsonfile).replace('\'','"'))
        with open("/tmp/output.log", "a") as output:
            subprocess.call("docker run name:Text2SpeechCensoringWorkflow_MergedFunction '"+ str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)

    if invokedFun == "Text2SpeechCensoringWorkflow_Compression":
        with open("/tmp/output.log", "a") as output:
            subprocess.call("docker run name:Text2SpeechCensoringWorkflow_Compression "+  str(jsonfile).replace('\'','"') + "' " + reqID , shell=True, stdout=output, stderr=output)
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
