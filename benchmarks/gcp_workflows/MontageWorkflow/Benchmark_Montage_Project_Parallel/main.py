import base64
import json
from datetime import datetime
from sys import getsizeof
import uuid
import random
import os
import shutil
import numpy as np
from google.cloud import storage
from MontagePy.main import mProjExec, mImgtbl

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def handler(request):
    request_json = request.get_json()
    req_id = request_json['reqID']
    color = request_json['color']
    index = request_json['index']
    fits_file_names = request_json['fitsFileNames']
    header_file_name = request_json['headerFileName']
    total_len = request_json['totalLen']

    print(fits_file_names)
    projected_dir = Montage_Project_Parallel(fits_file_names, header_file_name, color, req_id)

    message = {
      'headerFileName': header_file_name,
      'color': color,
      'projectedDir': projected_dir,
      'totalLen': total_len
    }

    if index == 0:
      return {
          'statusCode': 200,
          'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
          'body': {
              'data': {'message':message, 'reqID': req_id},
          }
      }
    else:
        return {}

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