import base64
import json
from datetime import datetime
from sys import getsizeof
import uuid
import random
import time
import os
import shutil
import numpy as np
from google.cloud import storage
from MontagePy.main import *

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def handler(request):
    request_json = request.get_json()
    req_id = request_json['reqID']
    projected_dir = request_json['projectedDir']
    color = request_json['color']
    table_file = request_json['rawTableFile']
    out_fit_file = request_json['fitsTableFile']

    corrected_dir = Montage_Background(projected_dir, table_file, out_fit_file, req_id, color)
    
    message = {
      'correctedDir': corrected_dir,
      'headerFileName': request_json['headerFileName'],
      'color': color
    }
        
    # Return
    return {
      'statusCode': 200,
      'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
      'body': {
          'data': {'message':message, 'reqID': req_id},
      }
    }

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