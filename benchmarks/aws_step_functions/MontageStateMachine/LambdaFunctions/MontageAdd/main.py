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
        
        corrected_dir = event['body']['data']['message']['correctedDir']
        header_file_name = event['body']['data']['message']['headerFileName']
        color = event['body']['data']['message']['color']
        reqID = event['body']['data']['reqID']
    
        result_dir = Montage_Add(corrected_dir, header_file_name, reqID, color)
        message = {
            'resultDir': result_dir,
        }
        
    if color == 'red':
        return {
            'statusCode': 200,
            'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'body': {
                'data': {'message':message, 'reqID': reqID},
            }
        }
    
def Montage_Add(corrected_dir, header_file_name, req_id, color):
    local_corrected_dir = download_corrected_dir(corrected_dir)
    print('downloaded corrected files')

    c_tblfile = '/tmp/cimages.tbl'
    status = mImgtbl(local_corrected_dir, c_tblfile)
    perror(status)
    print('mImgtbl done')

    local_header_path = '/tmp/header.hdr'
    bucket.download_file(header_file_name, local_header_path)

    local_out_file = '/tmp/result.fits'
    status = mAdd(local_corrected_dir, c_tblfile, local_header_path, local_out_file)
    perror(status)
    print('mAdd done')

    result_dir = f'result/{req_id}'
    bucket.upload_file(local_out_file, f'{result_dir}/{color}.fits')
    return result_dir

def download_corrected_dir(corrected_dir):
    local_corrected_dir = '/tmp/corrected'
    if os.path.exists(local_corrected_dir):
        shutil.rmtree(local_corrected_dir)
    os.makedirs(local_corrected_dir)
    objects = []
    for object_summary in bucket.objects.filter(Prefix=corrected_dir):
        objects.append(object_summary.key)
    for o in objects:
        if not o.endswith('.fits'):
            continue
        blob_name_base = o.split('/')[-1]
        bucket.download_file(o, f'{local_corrected_dir}/{blob_name_base}')
    return local_corrected_dir