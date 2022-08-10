from sklearn import datasets
import base64
import json
import datetime
import logging
import uuid
from random import randint
from sys import getsizeof
from google.cloud import datastore
from google.cloud import pubsub_v1
import numpy as np
import random


batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def getInput(request):
    routingKey = DSclient.key("routingDecision", "ChatBotWorkflow")
    routingEntity = DSclient.get(key=routingKey)
    active = routingEntity["active"]
    activeRouting = "routing" + "_" + str(active)
    routing = eval(routingEntity[activeRouting])
    # routing = eval(routingEntity["routing"])
    finalRouting = ""
    for function in routing:
      functionArray = np.array(function)
      if (np.all(functionArray==0)):
        finalRouting = finalRouting + "0"
      else:
        allpossibleVMs = [0]
        possibleVMs = list(np.where(functionArray != 0))[0]
        possibleVMs = np.array(possibleVMs)
        possibleVMs = possibleVMs + 1
        possibleVMs = list(possibleVMs)
        possiblePercentages = [function[i - 1] for i in possibleVMs]
        allpossibleVMs = allpossibleVMs + possibleVMs
        allpossiblePercentages = [1 - (np.sum(possiblePercentages))]
        allpossiblePercentages = allpossiblePercentages + possiblePercentages
        randomChoices = random.choices(allpossibleVMs, weights=allpossiblePercentages, k=1)
        finalChoice = randomChoices[0]
        if finalChoice == 0:
          finalRouting = finalRouting + "0"
        else:
          finalRouting = finalRouting + chr(64+int(finalChoice))
    print("Routing:::::", finalRouting)
    reqID = uuid.uuid4().hex
    # merging_key = DSclient.key("Merging", ("ChatBot" + reqID))
    # mergingEntity = datastore.Entity(key=merging_key)
    # mergingEntity.update(
    # {
    #     "Counter": 0,
    #     "Date" : datetime.datetime.utcnow(),
    #     "nextFunc" : "",
    #     "numBranches" : 2,
    #     "results": "{}"

    # }
    # )

    # DSclient.put(mergingEntity)
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        messageDict =  request.args.get('message')
    elif request_json and 'message' in request_json:
      messageDict =  request_json['message']
    fields = messageDict.split(", ")
    generatedMessageDict = {}
    for field in fields:
      insideDict = field.split(":")
      generatedMessageDict[insideDict[0]] = insideDict[1]
    Network_Bound = int(generatedMessageDict['Network_Bound'])
    bundle_size = int(generatedMessageDict["bundle_size"])
    skew = int(generatedMessageDict["skew"])
    # if request.args and 'Network_Bound' in request.args:
    #     Network_Bound =  request.args.get('Network_Bound')
    # elif request_json and 'Network_Bound' in request_json:
    #     Network_Bound =  request_json['Network_Bound']
    # if request.args and 'bundle_size' in request.args:
    #     bundle_size =  request.args.get('bundle_size')
    # elif request_json and 'bundle_size' in request_json:
    #     bundle_size =  request_json['bundle_size']
    # if request.args and 'skew' in request.args:
    #     skew =  request.args.get('skew')
    # elif request_json and 'skew' in request_json:
    #     skew =  request_json['skew']
    routingData = finalRouting
    message_json = json.dumps({
      'data': {'Network_Bound': Network_Bound, "bundle_size" : bundle_size, "skew": skew},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    routing = routingData[1]


    
    # 0 for serverless, 1 for VM
    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'ChatBot_Split')
      publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        vmNumber = ord(routing) - 64
        vmTopic = "vmTopic"+ str(vmNumber) 
        invokedFunction = "ChatBot_Split"
        topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
        publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
        publish_future.result()

    executionID = request.headers["Function-Execution-Id"]
    logging.warning(str(reqID))
    return executionID
