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
    routingKey = DSclient.key("routingDecision", "RegressionTuningWorkflow")
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
    merging_key = DSclient.key("Merging", ("RegressionTuning" + reqID))
    mergingEntity = datastore.Entity(key=merging_key)
    mergingEntity.update(
    {
        "Counter": 0,
        "Date" : datetime.datetime.utcnow(),
        "nextFunc" : "RegressionTuning_JoinRuns",
        "numBranches" : 2,
        "results": "{}"

    }
    )

    DSclient.put(mergingEntity)
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        samplesNum =  request.args.get('message')
    elif request_json and 'message' in request_json:
        samplesNum =  request_json['message']
    routingData = finalRouting
    message_json = json.dumps({
      'data': {'samplesNum': samplesNum},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    routing = routingData[1]


    
    # 0 for serverless, 1 for VM
    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'RegressionTuning_createDataset')
      publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(samplesNum)), routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        vmNumber = ord(routing) - 64
        vmTopic = "vmTopic"+ str(vmNumber) 
        invokedFunction = "RegressionTuning_createDataset"
        topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
        publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(samplesNum)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
        publish_future.result()

    executionID = request.headers["Function-Execution-Id"]
    logging.warning(str(reqID))
    return executionID
