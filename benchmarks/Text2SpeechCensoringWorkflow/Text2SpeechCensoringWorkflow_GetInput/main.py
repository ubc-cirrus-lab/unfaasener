import base64
import json
import datetime
import logging
import uuid
from sys import getsizeof
from google.cloud import datastore
from google.cloud import pubsub_v1
import numpy as np
import random

# Instantiates a Pub/Sub client
batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
# publisher = pubsub_v1.PublisherClient()
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()
def get(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    reqID = uuid.uuid4().hex
    # merging_key = DSclient.key("Merging", "Text2SpeechCensoringWorkflow_Censor")
    # mergingEntity = DSclient.get(key=merging_key)
    # mergingEntity["reqs"].append(str(reqID))
    # mergingEntity["Dates"].append(str(datetime.datetime.utcnow()))
    # mergingEntity["Counters"].append(0)
    # mergingEntity["results"].append("{}")
    # with DSclient.transaction():
    #   DSclient.put(mergingEntity)

    merging_key = DSclient.key("Merging", ("Text2SpeechCensoringWorkflow_Censor" + reqID))
    routingKey = DSclient.key("routingDecision", "Text2SpeechCensoringWorkflow")
    routingEntity = DSclient.get(key=routingKey)
    routing = eval(routingEntity["routing"])
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

    mergingEntity = datastore.Entity(key=merging_key)
    mergingEntity.update(
    {
        "Counter": 0,
        "Date" : datetime.datetime.utcnow(),
        "nextFunc" : "Text2SpeechCensoringWorkflow_Censor",
        "numBranches" : 2,
        "results": "{}"

    }
    )

    DSclient.put(mergingEntity)


    request_json = request.get_json()
    message = "Hello World"
    if request.args and 'message' in request.args:
        message =  request.args.get('message')
    elif request_json and 'message' in request_json:
        message =  request_json['message']

    
    # routingData = request_json.get("routing")
    routingData = finalRouting

    # First Branch
    routing = routingData[2]
    # 0 for serverless, 1 for VM

    message_json = json.dumps({
      'data': {'message': message},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex
    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-Text2Speech')
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
      vmNumber = ord(routing) - 64
      vmTopic = "vmTopic"+ str(vmNumber) 
      invokedFunction = "Text2SpeechCensoringWorkflow_Text2Speech"
      topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path, data=message_bytes, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()


    # Second Branch
    routing2 = routingData[1]
    # 0 for serverless, 1 for VM

    message_json2 = json.dumps({
      'data': {'message': message},
    })

    message_bytes2 = message_json.encode('utf-8')
    # msgID = uuid.uuid4().hex
    if routing2 == "0":
      topic_path2 = publisher.topic_path(PROJECT_ID, 'dag-Profanity')
      publish_future = publisher.publish(topic_path2, data=message_bytes2, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
      vmNumber = ord(routing2) - 64
      vmTopic = "vmTopic"+ str(vmNumber) 
      invokedFunction2 = "Text2SpeechCensoringWorkflow_Profanity"
      topic_path2 = publisher.topic_path(PROJECT_ID, vmTopic)
      publish_future = publisher.publish(topic_path2, data=message_bytes2, publishTime = str(datetime.datetime.utcnow()), identifier = msgID, reqID = str(reqID), msgSize = str(getsizeof(message)), invokedFunction = invokedFunction2, routing = routingData.encode('utf-8'))
      publish_future.result()

    logging.warning(str(reqID))
    executionID = request.headers["Function-Execution-Id"]
    return executionID
    


