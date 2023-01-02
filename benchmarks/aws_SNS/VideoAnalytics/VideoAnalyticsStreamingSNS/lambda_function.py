import json
from datetime import datetime
import boto3
import cv2
import sys 
import os

s3 = boto3.resource('s3')
bucket = s3.Bucket('videoanalyticsbenchmark')

def lambda_handler(event, context):
    
    if event == {}:
        print(f"Error: Event is empty")
    else:
        msg = event['Records'][0]['Sns']['Message']
        body = (json.loads(msg))['body']
        data = (json.loads(body))['data']
        
        videoName = data['videoName']
        fanoutNum = data['fanoutNum']
        req_id = data['reqID']
        
        video_name = VideoAnalytics_Streaming(videoName, req_id)
        
    # Return
    notification = json.dumps({
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'videoName': video_name, 'reqID': req_id, 'fanoutNum': fanoutNum},
        })
    })
    
    client = boto3.client('sns')
    response = client.publish (
      TargetArn = "arn:aws:sns:us-east-2:417140135939:VideoAnalytics_Decoder",
      Message = json.dumps({'default': notification}),
      MessageStructure = 'json'
   )
    
    return {
      'statusCode': 200,
      'body': json.dumps(response)
   }
    
# This function resized the specified video.
def VideoAnalytics_Streaming(filename, req_id):
    
    local_filename = f'/tmp/{filename}'
    bucket.download_file(filename, local_filename)
 
    resized_local_filename = resize_and_store(local_filename)
    streaming_filename = f'{req_id}-{filename}'
    bucket.upload_file(resized_local_filename, streaming_filename)

    os.remove(local_filename)
    os.remove(resized_local_filename)
    return streaming_filename
    
def resize_and_store(local_filename):
    cap = cv2.VideoCapture(local_filename)
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    resized_local_filename = '/tmp/resized_video.mp4'
    width, height = 340, 256
    writer = cv2.VideoWriter(resized_local_filename, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.resize(frame, (width, height))
        writer.write(frame)
    return resized_local_filename