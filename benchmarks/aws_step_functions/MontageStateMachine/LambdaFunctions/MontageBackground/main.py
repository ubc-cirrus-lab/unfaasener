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
        projected_dir = event['body']['data']['message']['projectedDir']
        color = event['body']['data']['message']['color']
        table_file = event['body']['data']['message']['rawTableFile']
        out_fit_file = event['body']['data']['message']['fitsTableFile']
        reqID = event['body']['data']['reqID']
    
        corrected_dir = Montage_Background(projected_dir, table_file, out_fit_file, reqID, color)
        message = {
        'correctedDir': corrected_dir,
        'headerFileName': event['body']['data']['message']['headerFileName'],
        'color': color,
        }
        
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'message':message, 'reqID': reqID},
        }
    }
    
def Montage_Background(projected_dir, table_file, out_fit_file, req_id, color):

    local_tblfile = '/tmp/rimage.tbl'
    bucket.download_file(table_file, local_tblfile)

    local_projected_dir = download_projected_dir(projected_dir)
    status = mImgtbl(local_projected_dir, local_tblfile)
    perror(status)
    print('mImgtbl done')

    local_out_fit_file = '/tmp/fits.tbl'
    bucket.download_file(out_fit_file, local_out_fit_file)

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
        bucket.upload_file(f'{local_corrected_dir}/{f}', f'{corrected_dir}/{f}')

    return corrected_dir

def download_projected_dir(projected_dir):
    local_projected_dir = '/tmp/projected'
    if os.path.exists(local_projected_dir):
        shutil.rmtree(local_projected_dir)
    os.makedirs(local_projected_dir)
    objects = []
    for object_summary in bucket.objects.filter(Prefix=projected_dir):
        objects.append(object_summary.key)
    for o in objects:
        if not o.endswith('.fits'):
            continue
        blob_name_base = o.split('/')[-1]
        bucket.download_file(o, f'{local_projected_dir}/{blob_name_base}')
    return local_projected_dir