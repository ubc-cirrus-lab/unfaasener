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
PROJECT_ID = '***'
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
    routingKey = DSclient.key("routingDecision", "ImageProcessingWorkflow")
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

    request_json = request.get_json()
    if request.args and 'message' in request.args:
        imageName =  request.args.get('message')
    elif request_json and 'message' in request_json:
        imageName =  request_json['message']
    routingData = finalRouting



    message_json = json.dumps({
      'data': {'imageName': imageName},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex


    # First Branch
    # routing = int(routingData[0])
    routing = routingData[1]
    reqID = uuid.uuid4().hex

    
    # 0 for serverless, 1 for VM
    if routing == "0":
      topic_path = publisher.topic_path(PROJECT_ID, 'ImageProcessing_Flip')
      publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        vmNumber = ord(routing) - 64
        vmTopic = "vmTopic"+ str(vmNumber) 
        invokedFunction = "ImageProcessing_Flip"
        topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
        publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
        publish_future.result()
    #   confidence = (ord(routing)-65)*2
    #   random = randint(0,100)
    #   if random <= confidence:
    #       invokedFunction = "ImageProcessing_Flip"
    #       topic_path = publisher.topic_path(PROJECT_ID, 'dag-test-vm')
    #       publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
    #       publish_future.result()

    #   else:
    #       topic_path = publisher.topic_path(PROJECT_ID, 'ImageProcessing_Flip')
    #       publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), routing = routingData.encode('utf-8'))
    #       publish_future.result()
    #   logging.warning("confidence:{}, random: {}, VM exe: {}".format(confidence, random, vmExe))



    executionID = request.headers["Function-Execution-Id"]
    logging.warning(str(reqID))
    return executionID
