import json
import boto3
from datetime import datetime
from MontagePy.main import mViewer
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
        result_dir = event[0]['body']['data']['message']['resultDir']
        reqID = event[0]['body']['data']['reqID']
        
        Montage_GenPng(result_dir, reqID)
    
        return {
            'statusCode': 200,
            'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
            'body': {
                'data': {'reqID': reqID},
            }
        }
    
def Montage_GenPng(result_dir, req_id):
    wait_all_files(result_dir, "/tmp/result")

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

    bucket.upload_file(local_result_path, f'result/{req_id}.png')
    print('uploaded final image')


def wait_all_files(result_dir, local_result_dir):
    max_retry = 50
    if os.path.exists(local_result_dir):
        shutil.rmtree(local_result_dir)
    os.makedirs(local_result_dir)
    for _ in range(max_retry):
        objects = []
        for object_summary in bucket.objects.filter(Prefix=result_dir):
            objects.append(object_summary.key)
        
        objects = [o for o in objects if o.endswith('.fits')]
        l = len(objects)
        print([o for o in objects])
        if l == 3:  # Now we have all red, blue, and ir
            for o in objects:
                blob_name_base = o.split('/')[-1]
                if blob_name_base not in ['red.fits', 'blue.fits', 'ir.fits']:
                    print(f'{req_id}: Invalid blob_name_base: {blob_name_base}')
                    exit(1)
                bucket.download_file(o, f'{local_result_dir}/{blob_name_base}')
            return local_result_dir
        print(f'only {l} files in {result_dir} when 3 files expected')
        time.sleep(10)
    print('max retry exceeded')
    exit(1)