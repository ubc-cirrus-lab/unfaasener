import json
from datetime import datetime
import boto3
import cv2

EXT = '.jpg'

class VideoDecoder:
    def __init__(self, filename, req_id, fanout_num):
        s3 = boto3.resource('s3')
        self.bucket = s3.Bucket('videoanalyticsbenchmark')
        # self.video_blob = self.bucket.blob(filename)
        self.req_id = req_id
        self.fanout_num = fanout_num

    def decode(self):
        '''video_bytes = self.video_blob.download_as_bytes()
        video_bytes = self.bucket.download_file(fileName)
        tmp = tempfile.NamedTemporaryFile(suffix='.mp4')
        tmp.write(video_bytes)
        tmp.seek(0)
        vidcap = cv2.VideoCapture(tmp.name)
        frames = []
        for i in range(self.fanout_num):
            _, image = vidcap.read()
            frames.append(cv2.imencode(EXT, image)[1].tobytes())
        return frames'''

    def upload(self, i, frame_bytes):
        '''filename = f'{self.req_id}-{i}{EXT}'
        blob = self.bucket.blob(filename)
        blob.upload_from_string(frame_bytes)
        return filename'''

def lambda_handler(event, context):
    
    if event == {}:
        filename = 'sample.mp4'
    else:
        filename = json.loads(event['body'])['data']['videoName']
        fanout_num = json.loads(event['body'])['data']['fanout_num'] # To do: Send it from stream
        req_id = json.loads(event['body'])['data']['reqID']
        
        filenames = VideoAnalytics_Decoder(video_name, req_id, fanout_num)
    
    # Return
    return {
        'statusCode': 200,
        'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'videoName': video_name},
        })
    }
    
def VideoAnalytics_Decoder(filename, req_id, fanout_num):
    decoder = VideoDecoder(filename, req_id, fanout_num)
    frames = decoder.decode()
    return [decoder.upload(i, frame) for i, frame in enumerate(frames)]

