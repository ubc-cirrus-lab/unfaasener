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
from MontagePy.main import mViewer
from google.cloud import pubsub_v1, storage


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
    routing = routing_data[6]
    req_id = event['attributes']['reqID']

    data = json.loads(base64.b64decode(event['data']).decode('utf-8'))
    result_dir = data['resultDir']
    Montage_GenPng(result_dir, req_id)


def Montage_GenPng(result_dir, req_id):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')
    wait_all_files(cli, result_dir, "/tmp/result")

    imgjson = """
    {
       "image_type":"png",
       "true_color":1.50,
       "font_scale":1.1,
       "blue_file": {
          "fits_file":"/tmp/result/blue.fits",
          "stretch_min":"-0.1s",
          "stretch_max":"max",
          "stretch_mode":"gaussian-log"
       },
       "green_file": {
          "fits_file":"/tmp/result/ir.fits",
          "stretch_min":"-0.1s",
          "stretch_max":"max",
          "stretch_mode":"gaussian-log"
       },
       "red_file": {
          "fits_file":"/tmp/result/red.fits",
          "stretch_min":"-0.1s",
          "stretch_max":"max",
          "stretch_mode":"gaussian-log"
       }
    }
    """

    local_result_path = '/tmp/result.png'
    status = mViewer(imgjson, local_result_path, mode=1)
    perror(status)

    blob = bucket.blob(f'result/{req_id}.png')
    blob.upload_from_filename(local_result_path)
    print('uploaded final image')


def wait_all_files(cli, result_dir, local_result_dir):
    max_retry = 50
    if os.path.exists(local_result_dir):
        shutil.rmtree(local_result_dir)
    os.makedirs(local_result_dir)
    for _ in range(max_retry):
        bucket = cli.bucket('montage_workflow')
        blobs = list(bucket.list_blobs(prefix=result_dir))
        blobs = [b for b in blobs if b.name.endswith('.fits')]
        l = len(blobs)
        print([b.name for b in blobs])
        if l == 3:  # Now we have all red, blue, and ir
            for blob in blobs:
                blob_name_base = blob.name.split('/')[-1]
                if blob_name_base not in ['red.fits', 'blue.fits', 'ir.fits']:
                    print(f'{req_id}: Invalid blob_name_base: {blob_name_base}')
                    exit(1)
                blob.download_to_filename(f'{local_result_dir}/{blob_name_base}')
            return local_result_dir
        print(f'only {l} files in {result_dir} when 3 files expected')
        time.sleep(10)
    print('max retry exceeded')
    exit(1)
