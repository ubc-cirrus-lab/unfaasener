import base64
import json
import datetime
from sys import getsizeof
import uuid
import random
import time
import os
import shutil

import numpy as np
from google.cloud import pubsub_v1, storage
from MontagePy.main import *

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
    projected_dir = data['projectedDir']
    color = data['color']
    table_file = data['rawTableFile']
    out_fit_file = data['fitsTableFile']

    corrected_dir = Montage_Background(projected_dir, table_file, out_fit_file, req_id, color)
    message = json.dumps({
        'correctedDir': corrected_dir,
        'headerFileName': data['headerFileName'],
        'color': color,
    }).encode('utf-8')
    next_fn = 'Montage_Add'
    msg_id = uuid.uuid4().hex
    if routing == '0':
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

def Montage_Background(projected_dir, table_file, out_fit_file, req_id, color):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')

    local_tblfile = '/tmp/rimage.tbl'
    blob = bucket.blob(table_file)
    blob.download_to_filename(local_tblfile)

    local_projected_dir = download_projected_dir(cli, projected_dir)
    status = mImgtbl(local_projected_dir, local_tblfile)
    perror(status)
    print('mImgtbl done')

    local_out_fit_file = '/tmp/fits.tbl'
    blob = bucket.blob(out_fit_file)
    blob.download_to_filename(local_out_fit_file)

    corrected_tblfile = '/tmp/correction.tbl'
    status = mBgModel(local_tblfile, local_out_fit_file, corrected_tblfile)
    perror(status)
    print('mBgModel done')

    local_corrected_dir = '/tmp/corrected'
    if os.path.exists(local_corrected_dir):
        shutil.rmtree(local_corrected_dir)
    os.makedirs(local_corrected_dir)
    status = mBgExec(local_projected_dir, local_tblfile, corrected_tblfile, local_corrected_dir)
    perror(status)
    print('mBgExec done')

    corrected_dir = f'work/corrected-{req_id}'
    for f in os.listdir(local_corrected_dir):
        blob = bucket.blob(f'{corrected_dir}/{f}')
        blob.upload_from_filename(f'{local_corrected_dir}/{f}', timeout=500)

    return corrected_dir

def download_projected_dir(cli, projected_dir):
    local_projected_dir = '/tmp/projected'
    if os.path.exists(local_projected_dir):
        shutil.rmtree(local_projected_dir)
    os.makedirs(local_projected_dir)
    bucket = cli.bucket('montage_workflow')
    blobs = bucket.list_blobs(prefix=projected_dir)
    for blob in blobs:
        if not blob.name.endswith('.fits'):
            continue
        blob_name_base = blob.name.split('/')[-1]
        blob.download_to_filename(f'{local_projected_dir}/{blob_name_base}')
    return local_projected_dir
