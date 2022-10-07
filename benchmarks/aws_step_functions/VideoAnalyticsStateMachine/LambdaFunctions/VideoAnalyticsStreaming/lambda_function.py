import json
from datetime import datetime
import boto3
import cv2


s3 = boto3.resource('s3')
bucket = s3.Bucket('videoanalyticsbenchmark')

def lambda_handler(event, context):
    
    if event == {}:
        filename = 'sample.mp4'
    else:
        filename = json.loads(event['body'])['data']['videoName']
        req_id = json.loads(event['body'])['data']['reqID']
        
        video_name = VideoAnalytics_Streaming(filename, req_id)
        
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'videoName': video_name},
        })
    }
    
# This function resized the specified video.
def VideoAnalytics_Streaming(filename, req_id):
    
    local_filename = f'/tmp/{filename}'
    bucket.download_file(fileName, local_filename)
 
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
