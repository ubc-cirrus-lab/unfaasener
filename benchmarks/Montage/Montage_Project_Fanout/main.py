import base64
import json
import datetime
from sys import getsizeof
import uuid
import random

import numpy as np
from google.cloud import pubsub_v1, storage

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def handler(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    routing_data = event['attributes']['routing']
    routing = routing_data[1]
    req_id = event['attributes']['reqID']

    data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    header_file_name = data['headerFileName']
    color = data['color']
    fanout_num = data['fanoutNum']

    blobs = Montage_Project_Fanout(color)
    total_len = len(blobs)
    sizes = sizes_to_divide(total_len, fanout_num)

    next_fn = 'Montage_Project_Parallel'
    if routing == '0':
        cur = 0
        for i, size in enumerate(sizes):
            file_names = [blob.name for blob in blobs[cur:cur+size]]
            message = json.dumps({
                'fitsFileNames': file_names,
                'headerFileName': header_file_name,
                'color': color,
                'index': i,
                'totalLen': total_len,
            }).encode('utf-8')
            msg_id = uuid.uuid4().hex
            topic_path = publisher.topic_path(PROJECT_ID, next_fn)
            publish_future = publisher.publish(
                topic_path,
                data=message,
                reqID=req_id,
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msg_id,
                msgSize=str(getsizeof(message)),
                routing=routing_data.encode('utf-8'),
            )
            cur += size
    else:
        cur = 0
        for i, size in enumerate(sizes):
            file_names = [blob.name for blob in blobs[cur:cur+size]]
            vm_topic = f'vmTopic{ord(routing) - 64}'
            message = json.dumps({
                'fitsFileNames': file_names,
                'headerFileName': header_file_name,
                'color': color,
                'index': i,
                'totalLen': total_len,
            }).encode('utf-8')
            msg_id = uuid.uuid4().hex
            topic_path = publisher.topic_path(PROJECT_ID, vm_topic)
            publish_future = publisher.publish(
                topic_path,
                data=message,
                reqID=req_id,
                publishTime=str(datetime.datetime.utcnow()),
                identifier=msg_id,
                msgSize=str(getsizeof(message)),
                invokedFunction=next_fn,
                routing=routing_data.encode('utf-8'),
            )
            cur += size
    publish_future.result()

def Montage_Project_Fanout(color):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')
    li = list(bucket.list_blobs(prefix=f'data/{color}/'))
    return [f for f in li if f.name.endswith('.fits')]

def sizes_to_divide(total_len, fanout_num):
    base = total_len // fanout_num
    rest = total_len - base * fanout_num
    ret = []
    for i in range(fanout_num):
        ret.append(base + 1 if i < rest else base)
    return ret
