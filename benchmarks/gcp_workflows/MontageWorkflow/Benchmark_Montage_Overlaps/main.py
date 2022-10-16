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
    header_file_name = request_json['headerFileName']
    color = request_json['color']
    projected_dir = request_json['projectedDir']
    total_len = request_json['totalLen']

    res = Montage_Overlaps(total_len, projected_dir, req_id, header_file_name, color)
    res['projectedDir'] = projected_dir
    res['color'] = color
    res['headerFileName'] = header_file_name


    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message':res, 'reqID': req_id},
        }
    }


def Montage_Overlaps(total_len, projected_dir, req_id, header, color):
    cli = storage.Client()
    bucket = cli.bucket('montage_workflow')

    local_tblfile = '/tmp/rimage.tbl'
    local_projected_dir = wait_all_files(cli, total_len, projected_dir)
    status = mImgtbl(local_projected_dir, local_tblfile)
    perror(status)
    local_diff_file = '/tmp/diff.tbl'
    status = mOverlaps(local_tblfile, local_diff_file)
    perror(status)
    print(f'{req_id}: overlap done')

    local_header_path = '/tmp/header.hdr'
    blob = bucket.blob(header)
    blob.download_to_filename(local_header_path)
    out_fit_file = '/tmp/fits.tbl'
    status = mDiffFitExec(local_projected_dir, local_diff_file, local_header_path, '/tmp/diffs', out_fit_file)
    perror(status)
    print(f'{req_id}: mDiffFitExec')

    tblfile = f'work-{req_id}/{color}-rimage.tbl'
    blob = bucket.blob(tblfile)
    blob.upload_from_filename(local_tblfile)

    fits_table_file = f'work-{req_id}/{color}-fits.tbl'
    blob = bucket.blob(fits_table_file)
    blob.upload_from_filename(out_fit_file)

    return {
        'rawTableFile': tblfile,
        'fitsTableFile': fits_table_file,
    }

def wait_all_files(cli, total_len, projected_dir):
    max_retry = 40
    local_projected_dir = '/tmp/projected'
    if os.path.exists(local_projected_dir):
        shutil.rmtree(local_projected_dir)
    os.makedirs(local_projected_dir)
    for _ in range(max_retry):
        bucket = cli.bucket('montage_workflow')
        blobs = list(bucket.list_blobs(prefix=projected_dir))
        l = len(blobs)
        if l == total_len * 2:  # *.fits file and *_area.fits are generated.
            for blob in blobs:
                blob_name_base = blob.name.split('/')[-1]
                blob.download_to_filename(f'{local_projected_dir}/{blob_name_base}')
            return local_projected_dir
        print(f'only {l} files in {projected_dir} while {total_len * 2} files expected. waiting 10 seconds')
        time.sleep(10)
    print('max retry exceeded')
    exit(1)