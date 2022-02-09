import base64
import json
import datetime
import logging
import uuid
from sys import getsizeof
from google.cloud import datastore
from google.cloud import pubsub_v1

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
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
    request_json = request.get_json()
    if request.args and 'message' in request.args:
        imageName =  request.args.get('message')
    elif request_json and 'message' in request_json:
        imageName =  request_json['message']
    routingData = request_json.get("routing")

    # First Branch
    routing = int(routingData[0])
    reqID = uuid.uuid4().hex
    # 0 for serverless, 1 for VM


    if routing == 1:
      invokedFunction = "ImageProcessing_Flip"
      topic_path = publisher.topic_path(PROJECT_ID, 'dag-test-vm')
    else:
      topic_path = publisher.topic_path(PROJECT_ID, 'ImageProcessing_Flip')


    message_json = json.dumps({
      'data': {'imageName': imageName},
    })

    message_bytes = message_json.encode('utf-8')
    msgID = uuid.uuid4().hex

    if routing == 1:
      publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), invokedFunction = invokedFunction, routing = routingData.encode('utf-8'))
      publish_future.result()
    else:
        publish_future = publisher.publish(topic_path, data=message_bytes, reqID = str(reqID), publishTime = str(datetime.datetime.utcnow()), identifier = msgID, msgSize = str(getsizeof(imageName)), routing = routingData.encode('utf-8'))
        publish_future.result()
    executionID = request.headers["Function-Execution-Id"]
    logging.warning(str(reqID))
    return executionID
