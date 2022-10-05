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
    routing = routing_data[5]
    req_id = event['attributes']['reqID']

    data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    corrected_dir = data['correctedDir']
    header_file_name = data['headerFileName']
    color = data['color']

    result_dir = Montage_Add(corrected_dir, header_file_name, req_id, color)
    if color == 'red':  # invoke PubSub only when processing red images
        message = json.dumps({
            'resultDir': result_dir,
        }).encode('utf-8')
        next_fn = 'Montage_GenPng'
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

def Montage_Add(corrected_dir, header_file_name, req_id, color):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')

    local_corrected_dir = download_corrected_dir(cli, corrected_dir)
    print('downloaded corrected files')

    c_tblfile = '/tmp/cimages.tbl'
    status = mImgtbl(local_corrected_dir, c_tblfile)
    perror(status)
    print('mImgtbl done')

    local_header_path = '/tmp/header.hdr'
    blob = bucket.blob(header_file_name)
    blob.download_to_filename(local_header_path)

    local_out_file = '/tmp/result.fits'
    status = mAdd(local_corrected_dir, c_tblfile, local_header_path, local_out_file)
    perror(status)
    print('mAdd done')

    result_dir = f'result/{req_id}'
    blob = bucket.blob(f'{result_dir}/{color}.fits')
    blob.upload_from_filename(local_out_file, timeout=500)
    return result_dir

def download_corrected_dir(cli, corrected_dir):
    local_corrected_dir = '/tmp/corrected'
    if os.path.exists(local_corrected_dir):
        shutil.rmtree(local_corrected_dir)
    os.makedirs(local_corrected_dir)
    bucket = cli.bucket('montage_workflow')
    blobs = bucket.list_blobs(prefix=corrected_dir)
    for blob in blobs:
        if not blob.name.endswith('.fits'):
            continue
        blob_name_base = blob.name.split('/')[-1]
        blob.download_to_filename(f'{local_corrected_dir}/{blob_name_base}')
    return local_corrected_dir
