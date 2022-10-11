import json
import boto3
from datetime import datetime


s3 = boto3.resource('s3')
bucket = s3.Bucket('montagebenchmark')

def lambda_handler(event, context):
    
    if event:
        header_file_name = event['headerFileName']
        color = event['color']
        fanout_num = event['fanoutNum']
        reqID = event['reqID']
        
        objects = Montage_Fanout(color)
        total_len = len(objects)
        sizes = sizes_to_divide(total_len, fanout_num)
        
        messages = []
        cur = 0
        for i, size in enumerate(sizes):
            file_names = [o for o in objects[cur:cur+size]]
            messages.append({
                'fitsFileNames': file_names,
                'headerFileName': header_file_name,
                'color': color,
                'index': i,
                'totalLen': total_len,
                'reqID': reqID
            })
            cur += size
        
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': {
            'data': {'messages':messages, 'reqID': reqID},
        }
    }
    
def Montage_Fanout(color):
    result = []
    for object_summary in bucket.objects.filter(Prefix=f'data/{color}/'):
        if object_summary.key.endswith('.fits'):
            result.append(object_summary.key)
    return result
    
def sizes_to_divide(total_len, fanout_num):
    base = total_len // fanout_num
    rest = total_len - base * fanout_num
    ret = []
    for i in range(fanout_num):
        ret.append(base + 1 if i < rest else base)
    return ret