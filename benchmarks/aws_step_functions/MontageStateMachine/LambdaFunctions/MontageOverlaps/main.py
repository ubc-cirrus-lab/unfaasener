import json
import boto3
from datetime import datetime
from MontagePy.main import *
import os 
import sys
import shutil

s3 = boto3.resource('s3')
bucket = s3.Bucket('montagebenchmark')

def perror(status):
    if int(status['status']) == 1:
        print(status['msg'])
        exit(1)

def lambda_handler(event, context):
    
    if event:
        header_file_name = event[0]['body']['data']['message']['headerFileName']
        color = event[0]['body']['data']['message']['color']
        projected_dir = event[0]['body']['data']['message']['projectedDir']
        total_len = event[0]['body']['data']['message']['totalLen']
        reqID = event[0]['body']['data']['reqID']
    
        res = Montage_Overlaps(total_len, projected_dir, reqID, header_file_name, color)
        res['projectedDir'] = projected_dir
        res['color'] = color
        res['headerFileName'] = header_file_name
    
        
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message':res, 'reqID': reqID},
        }
    }
    
def Montage_Overlaps(total_len, projected_dir, req_id, header, color):

    local_tblfile = '/tmp/rimage.tbl'
    local_projected_dir = wait_all_files(total_len, projected_dir)
    status = mImgtbl(local_projected_dir, local_tblfile)
    perror(status)
    local_diff_file = '/tmp/diff.tbl'
    status = mOverlaps(local_tblfile, local_diff_file)
    perror(status)
    print(f'{req_id}: overlap done')

    local_header_path = '/tmp/header.hdr'
    bucket.download_file(header, local_header_path)
    out_fit_file = '/tmp/fits.tbl'
    status = mDiffFitExec(local_projected_dir, local_diff_file, local_header_path, '/tmp/diffs', out_fit_file)
    perror(status)
    print(f'{req_id}: mDiffFitExec')

    tblfile = f'work-{req_id}/{color}-rimage.tbl'
    bucket.upload_file(local_tblfile, tblfile)

    fits_table_file = f'work-{req_id}/{color}-fits.tbl'
    bucket.upload_file(out_fit_file, fits_table_file)

    return {
        'rawTableFile': tblfile,
        'fitsTableFile': fits_table_file,
    }
    
def wait_all_files(total_len, projected_dir):
    max_retry = 40
    local_projected_dir = '/tmp/projected'
    if os.path.exists(local_projected_dir):
        shutil.rmtree(local_projected_dir)
    os.makedirs(local_projected_dir)
    for _ in range(max_retry):
        objects = []
        for object_summary in bucket.objects.filter(Prefix=projected_dir):
            objects.append(object_summary.key)
        l = len(objects)
        if l == total_len * 2:  # *.fits file and *_area.fits are generated.
            for o in objects:
                blob_name_base = o.split('/')[-1]
                bucket.download_file(o, f'{local_projected_dir}/{blob_name_base}')
            return local_projected_dir
        print(f'only {l} files in {projected_dir} while {total_len * 2} files expected. waiting 10 seconds')
        time.sleep(10)
    print('max retry exceeded')
    exit(1)