
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
project_id = "ubc-serverless-ghazal"
subscription_id = "vm-sub"
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
    if invokedFun == "Text2SpeechCensoringWorkflow_Text2Speech":
        filename = Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Text2Speech(decodedMessage.get("message"), reqID)
        #Mohamed has to add here
        with open("/tmp/output.log", "a") as output:
            subprocess.call("python3 vmContainerizer.py"+functionname + " " + decodedMessage.get("message") + " " + reqID , shell=True, stdout=output, stderr=output)
        routing = int(routingData[2])
        publishedJson = json.dumps({'data':{'message': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunction = "Text2SpeechCensoringWorkflow_Conversion"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'dag-Conversion')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "Text2SpeechCensoringWorkflow_Conversion":
        fileName = Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Conversion(decodedMessage.get("message"), reqID)
        publishedJson = json.dumps({'data':{'message': fileName}})
        publishedData = publishedJson.encode("utf-8")
        routing = int(routingData[3])
        if routing == 1:
            invokedFunction = "Text2SpeechCensoringWorkflow_Compression"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'Text2SpeechCensoringWorkflow_Compression')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "Text2SpeechCensoringWorkflow_Profanity":
        message = Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Profanity(decodedMessage.get("message"))
        publishedJson = json.dumps({'data':{'message': message}})
        publishedData = publishedJson.encode("utf-8")
        routing = int(routingData[4])
        if routing == 1:
            invokedFunction = "Text2SpeechCensoringWorkflow_MergingPoint"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)),invokedFunction = invokedFunction, routing = routingData.encode("utf-8"), messageContent = "indexes", branchName = "Text2SpeechCensoringWorkflow_Censor")
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'dag-MergingPoint')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"), messageContent = "indexes", branchName = "Text2SpeechCensoringWorkflow_Censor")
            publish_future.result()
    if invokedFun == "Text2SpeechCensoringWorkflow_MergingPoint":
        datastore_client = datastore.Client()
        kind = "Merging"
        name = (message.attributes.get('branchName') ) + ( message.attributes.get('reqID') )
        reqID = (message.attributes.get('reqID'))
        merge_key = datastore_client.key(kind, name)
        merge = datastore_client.get(key=merge_key)
        nextFunction = (merge["nextFunc"])
        newTotal = merge['numBranches']
        prevCounter = merge["Counter"]
        newCounter = prevCounter+1
        merge["Counter"] = newCounter
        resJson = (json.loads(merge["results"]))
        content = message.attributes.get('messageContent')
        valueContent = decodedMessage.get("message")
        newJson = {content : valueContent}
        resJson.update(newJson)
        merge["results"]= json.dumps(resJson)
        message = (json.loads(merge["results"]))
        if (newCounter == newTotal):
            routing = int(routingData[5])
            message_json = json.dumps({
                'data': message,
            })
            message_bytes = message_json.encode('utf-8')
            msgID = uuid.uuid4().hex

            if routing == 1:
                invokedFunction = nextFunction
                topic_path = publisher.topic_path(project_id, 'dag-test-vm')
                publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode("utf-8"))
                publish_future.result()
            else:
                topic_path = publisher.topic_path(project_id, "dag-Censor")
                publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID),msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"))
                publish_future.result() 
            datastore_client.delete(merge_key)
            logging.warning(str(reqID))
        else:
            datastore_client.put(merge)

    if invokedFun == "Text2SpeechCensoringWorkflow_Compression":
        filename = Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Compression(decodedMessage.get("message"), reqID)
        routing = int(routingData[4])
        publishedJson = json.dumps({'data':{'message': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunctionPublish = "Text2SpeechCensoringWorkflow_MergingPoint"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()),  reqID =str(reqID),invokedFunction = invokedFunctionPublish, routing = routingData.encode("utf-8"), messageContent = "convertedFileName", branchName = "Text2SpeechCensoringWorkflow_Censor")
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'dag-MergingPoint')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode("utf-8"), messageContent = "convertedFileName", branchName = "Text2SpeechCensoringWorkflow_Censor")
            publish_future.result()
    if invokedFun == "Text2SpeechCensoringWorkflow_Censor":
        print(decodedMessage.get("indexes"))
        print(type(decodedMessage.get("indexes")))
        Text2SpeechWorkflow.Text2SpeechCensoringWorkflow_Censor(decodedMessage.get("convertedFileName"), decodedMessage.get("indexes"), reqID)
        print("Executing the workflow is done!")
    if invokedFun == "ImageProcessing_Flip":
        filename = ImageProcessing.ImageProcessing_Flip(decodedMessage.get("imageName"), reqID)
        routing = int(routingData[1])
        publishedJson = json.dumps({'data':{'imageName': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunction = "ImageProcessing_Rotate"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'ImageProcessing_Rotate')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "ImageProcessing_Rotate":
        filename = ImageProcessing.ImageProcessing_Rotate(decodedMessage.get("imageName"), reqID)
        routing = int(routingData[2])
        publishedJson = json.dumps({'data':{'imageName': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunction = "ImageProcessing_Filter"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'ImageProcessing_Filter')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "ImageProcessing_Filter":
        filename = ImageProcessing.ImageProcessing_Filter(decodedMessage.get("imageName"), reqID)
        routing = int(routingData[3])
        publishedJson = json.dumps({'data':{'imageName': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunction = "ImageProcessing_Greyscale"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'ImageProcessing_Greyscale')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "ImageProcessing_Greyscale":
        filename = ImageProcessing.ImageProcessing_Greyscale(decodedMessage.get("imageName"), reqID)
        routing = int(routingData[4])
        publishedJson = json.dumps({'data':{'imageName': filename}})
        publishedData = publishedJson.encode("utf-8")
        if routing == 1:
            invokedFunction = "ImageProcessing_Resize"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'ImageProcessing_Resize')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID), routing = routingData.encode('utf-8'))
            publish_future.result()
    if invokedFun == "ImageProcessing_Resize":
        filename = ImageProcessing.ImageProcessing_Resize(decodedMessage.get("imageName"), reqID)
        publishedJson = json.dumps({'data':{'message': filename}})
        publishedData = publishedJson.encode("utf-8")
        topic_path = publisher.topic_path(project_id, 'imageprocessing_GC')
        publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = str(reqID))
        publish_future.result()
    if invokedFun == "func1":
        func1(message.data)
        routing = int(routingData[1])
        secondRouting = int(routingData[2])
        publishedjson = json.dumps({'data': {'message' : "message published by first funcrion in the VM"}})
        publishedData = publishedjson.encode("utf-8")
        msgIDPublish = uuid.uuid4().hex
        mergingID = uuid.uuid4().hex
        merging_key = DSclient.key("Merging", mergingID)
        mergingEntity = datastore.Entity(key=merging_key)
        mergingEntity.update({"numBranches" : 2, "triggeredBranchesCounter" : 0, "reqID": mergingID, "DateCreated":datetime.datetime.utcnow() })
        DSclient.put(mergingEntity)
        if routing == 1:
            invokedFunctionPublish = "func2"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, reqID = message.attributes.get("reqID"), mergingID = mergingID, msgSize = str(getsizeof(message)), invokedFunction = invokedFunctionPublish, routing = routingData.encode("utf-8"))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'chain-dag-test')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, reqID = message.attributes.get("reqID"), mergingID = mergingID, msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"))
            publish_future.result()
        if secondRouting == 1:
            secondinvokedFunctionPublish = "branch2"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, reqID = message.attributes.get("reqID"), mergingID = mergingID, msgSize = str(getsizeof(message)), invokedFunction = secondinvokedFunctionPublish, routing = routingData.encode("utf-8"))
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'secondBranch')
            publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, reqID = message.attributes.get("reqID"), mergingID = mergingID, msgSize = str(getsizeof(message)), routing = routingData.encode("utf-8"))
            publish_future.result()
    elif invokedFun == "func2":
        func2(message.data)
        publishedjson = json.dumps({'data': {'message' : "done-f1"}})
        publishedData = publishedjson.encode("utf-8")
        msgIDPublish = uuid.uuid4().hex
        topic_path = publisher.topic_path(project_id, 'Merging')
        publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), reqID = message.attributes.get("reqID"), mergingID = message.attributes.get("mergingID"),identifier = msgIDPublish, msgSize = str(getsizeof(message)), branch = "first", routing = routingData.encode("utf-8"))
    elif invokedFun == "branch2":
        branch2(message.data)
        msgIDPublish = uuid.uuid4().hex
        publishedjson = json.dumps({'data': {'message' : "done-f2"}})
        publishedData = publishedjson.encode("utf-8")
        topic_path = publisher.topic_path(project_id, 'Merging')
        publish_future = publisher.publish(topic_path, data=publishedData, publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, reqID = message.attributes.get("reqID"), mergingID = message.attributes.get("mergingID"), msgSize = str(getsizeof(message)), branch = "second",routing = routingData.encode("utf-8"))
    elif invokedFun == "merged":
        merged(message.data)
    elif invokedFun == "seqChained2":
        n, startTimes, retTimes = seqChained2(message.data, message.attributes.get("startTimes"), message.attributes.get("retTimes"))
        print(f"sent number : {n}")
        routing = int(routingData[1])
        msgIDPublish = uuid.uuid4().hex
        if routing == 1:
            invokedFunctionPublish = "seqChained3"
            topic_path = publisher.topic_path(project_id, 'dag-test-vm')
            publish_future =publisher.publish(topic_path, json.dumps({'data': {'n': str(n)}}).encode("utf-8"), retTimes = json.dumps(retTimes), startTimes = json.dumps(startTimes), publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, msgSize = str(getsizeof(message)), invokedFunction = invokedFunctionPublish, routing = routingData) 
            publish_future.result()
        else:
            topic_path = publisher.topic_path(project_id, 'seqChained3')
            publish_future = publisher.publish(topic_path, json.dumps({'data': {'n': str(n)}}).encode("utf-8"), retTimes = json.dumps(retTimes), startTimes =json.dumps(startTimes), publishTime = str(datetime.datetime.utcnow()), identifier = msgIDPublish, msgSize = str(getsizeof(message)), routing = routingData) 
            publish_future.result()
    elif invokedFun == "seqChained3":
        seqChained3(message.data, message.attributes.get("startTimes"), message.attributes.get("retTimes"))
    with open('data.json', 'w') as outfile:
        json.dump(writtenData, outfile)

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
