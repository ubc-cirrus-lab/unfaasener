import json
import datetime
from sys import getsizeof
import uuid
import random

import numpy as np
from google.cloud import datastore, pubsub_v1, storage
from MontagePy.main import *


batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'
DSclient = datastore.Client()

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

"""
Sample input json
{
    "resolution": 1.0,
    "size": 2,
    "coordinateSystem": "Equatorial",
    "location": "M31",
    "fanoutNum": 4
}
"""
def handler(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    # todo(joe): change dsclient name
    routingKey = DSclient.key('routingDecision', 'MontageWorkflow')
    routingEntity = DSclient.get(key=routingKey)
    active = routingEntity['active']
    activeRouting = f'routing_{active}'
    routing = eval(routingEntity[activeRouting])
    finalRouting = ''
    for function in routing:
        functionArray = np.array(function)
        if np.all(functionArray==0):
            finalRouting += '0'
        else:
            allpossibleVMs = [0]
            possibleVMs = list(np.where(functionArray != 0))[0]
            possibleVMs = np.array(possibleVMs)
            possibleVMs = possibleVMs + 1
            possibleVMs = list(possibleVMs)
            possiblePercentages = [function[i - 1] for i in possibleVMs]
            allpossibleVMs += possibleVMs
            allpossiblePercentages = [1 - (np.sum(possiblePercentages))]
            allpossiblePercentages += possiblePercentages
            randomChoices = random.choices(allpossibleVMs, weights=allpossiblePercentages, k=1)
            finalChoice = randomChoices[0]
            if finalChoice == 0:
                finalRouting += '0'
            else:
                finalRouting += chr(64 + int(finalChoice))
    print('Routing:::::', finalRouting)

    # First Branch
    routing = finalRouting[1]
    reqID = uuid.uuid4().hex

    request_json = request.get_json()
    resolution = request_json['resolution']
    location = request_json['location']
    coordinate_system = request_json['coordinateSystem']
    size = request_json['size']
    fanout_num = request_json['fanoutNum']

    if not resolution or not location or not coordinate_system or not size or not fanout_num:
        print(f'malformed request json: {request_json}')
        exit(1)

    local_header_path = '/tmp/Montage.hdr'
    status = mHdr(location, size, size, local_header_path, resolution=resolution, csys=coordinate_system)
    perror(status)

    header_filename = f'header-{reqID}.hdr'
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')
    blob = bucket.blob(header_filename)
    blob.upload_from_filename(local_header_path)

    next_fn = 'Montage_Project_Fanout'
    # 0 for serverless, 1 for VM
    for color in ['red', 'blue', 'ir']:
        message_json = json.dumps({
            'headerFileName': header_filename,
            'color': color,
            'fanoutNum': fanout_num,
        })

        message_bytes = message_json.encode('utf-8')
        msgID = uuid.uuid4().hex
        if routing == '0':
            topic_path = publisher.topic_path(PROJECT_ID, next_fn)
            publish_future = publisher.publish(
                topic_path,
                data=message_bytes,
                reqID=reqID,
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msgID,
                msgSize=str(getsizeof(message_bytes)),
                routing=finalRouting.encode('utf-8'),
            )
        else:
            vmTopic = f'vmTopic{ord(routing) - 64}'
            topic_path = publisher.topic_path(PROJECT_ID, vmTopic)
            publish_future = publisher.publish(
                topic_path,
                data=message_bytes,
                reqID=f'{reqID}-{color}',
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msgID,
                msgSize=str(getsizeof(message_bytes)),
                invokedFunction=next_fn,
                routing=finalRouting.encode('utf-8'),
            )

    publish_future.result()
    executionID = request.headers['Function-Execution-Id']
    print(reqID)
    return executionID
