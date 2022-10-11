import json
import boto3
from datetime import datetime
from MontagePy.main import mProjExec, mImgtbl
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
    
        color = event['color']
        index = event['index']
        fits_file_names = event['fitsFileNames']
        header_file_name = event['headerFileName']
        total_len = event['totalLen']
        reqID = event['reqID']
    
        print(fits_file_names)
        projected_dir = Montage_Project_Parallel(fits_file_names, header_file_name, color, reqID)
        
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
                'data': {'message':message, 'reqID': reqID},
            }
        }
        
    
def Montage_Project_Parallel(fits_files, header_file_name, color, req_id):
    local_header_path = '/tmp/header.hdr'
    local_fits_dir = '/tmp/raw'
    if os.path.exists(local_fits_dir):
        shutil.rmtree(local_fits_dir)
    os.makedirs(local_fits_dir)

    bucket.download_file(header_file_name, local_header_path)    

    for file in fits_files:
        base = file.split('/')[-1]
        bucket.download_file(file, f'{local_fits_dir}/{base}')

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
        bucket.upload_file(f'{local_projected_dir}/{f}', f'{projected_dir}/{f}')
    return projected_dir