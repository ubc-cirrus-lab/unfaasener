import base64
import json
import datetime
from sys import getsizeof
import uuid
import random
import os
import shutil

import numpy as np
from google.cloud import pubsub_v1, storage
from MontagePy.main import mProjExec, mImgtbl

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
    color = data['color']
    index = data['index']
    fits_file_names = data['fitsFileNames']
    header_file_name = data['headerFileName']
    total_len = data['totalLen']

    print(fits_file_names)
    projected_dir = Montage_Project_Parallel(fits_file_names, header_file_name, color, req_id)

    if index == 0:  # invoke PubSub only when processing the first projection.
        print('index is 0, calling Montage_Overlaps')
        next_fn = 'Montage_Overlaps'
        if routing == '0':
            message = json.dumps({
                'headerFileName': header_file_name,
                'color': color,
                'projectedDir': projected_dir,
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
        else:
            vm_topic = f'vmTopic{ord(routing) - 64}'
            message = json.dumps({
                'headerFileName': header_file_name,
                'color': color,
                'projectedDir': projected_dir,
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

def Montage_Project_Parallel(fits_files, header_file_name, color, req_id):
    local_header_path = '/tmp/header.hdr'
    local_fits_dir = '/tmp/raw'
    if os.path.exists(local_fits_dir):
        shutil.rmtree(local_fits_dir)
    os.makedirs(local_fits_dir)

    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')

    blob = bucket.blob(header_file_name)
    blob.download_to_filename(local_header_path)

    for file in fits_files:
        blob = bucket.blob(file)
        base = file.split('/')[-1]
        blob.download_to_filename(f'{local_fits_dir}/{base}')

    tblfile = f'/tmp/rimages.tbl'
    status = mImgtbl(local_fits_dir, tblfile)
    perror(status)

    local_projected_dir = '/tmp/projected'
    if os.path.exists(local_projected_dir):
        shutil.rmtree(local_projected_dir)
    os.makedirs(local_projected_dir)

    print(f'{req_id}: started projection')
    status = mProjExec(local_fits_dir, tblfile, local_header_path, projdir=local_projected_dir, quickMode=True)
    perror(status)
    print(f'{req_id}: end projection')

    projected_dir = f'projected/{req_id}-{color}'
    for f in os.listdir(local_projected_dir):
        blob = bucket.blob(f'{projected_dir}/{f}')
        blob.upload_from_filename(f'{local_projected_dir}/{f}', timeout=500)
    return projected_dir
