import base64
import datetime
import json
import logging
import os
from sys import getsizeof
import uuid

from google.cloud import storage, pubsub_v1

batch_settings = pubsub_v1.types.BatchSettings(
    max_latency=0.001,  # default 10 ms
)
publisher = pubsub_v1.PublisherClient(batch_settings)
PROJECT_ID = 'ubc-serverless-ghazal'

def streaming(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    routing_data = event['attributes']['routing']
    routing = routing_data[2]
    req_id = event['attributes']['reqID']
    filename = json.loads(base64.b64decode(event['data']).decode('utf-8'))['data']['videoName']
    video_name = VideoAnalytics_Streaming(filename, req_id)
    message = json.dumps({
        'data': {'videoName': video_name}
    }).encode('utf-8')
    msg_id = uuid.uuid4().hex

    next_fn = 'VideoAnalytics_Decoder'
    if routing == '0':
        topic_path = publisher.topic_path(PROJECT_ID, next_fn)
        publish_future = publisher.publish(
            topic_path,
            data=message,
            reqID=req_id,
            publishTime=str(datetime.datetime.utcnow()),
            identifier=msg_id,
            msgSize=str(getsizeof(video_name)),
            routing=routing_data.encode('utf-8'),
        )
    else:
        vm_topic = f'vmTopic{ord(routing) - 64}'
        topic_path = publisher.topic_path(PROJECT_ID, vm_topic)
        publish_future = publisher.publish(
            topic_path,
            data=message,
            reqID=req_id,
            publishTime=str(datetime.datetime.utcnow()),
            identifier=msg_id,
            msgSize=str(getsizeof(video_name)),
            invokedFunction=next_fn,
            routing=routing_data.encode('utf-8'),
        )
    publish_future.result()
    logging.warning(req_id)

# This function pretends to strema a video.
# All it does is downloading a video from a bucket and uploading to another.
def VideoAnalytics_Streaming(filename, req_id):
    local_filename = f'/tmp/{filename}'

    cli = storage.Client()
    src_bucket = cli.bucket('videoanalyticsworkflow-storage-src')
    src_blob = src_bucket.blob(filename)
    src_blob.download_to_filename(local_filename)

    streaming_filename = f'{req_id}-{filename}'

    dst_bucket = cli.bucket('videoanalyticsworkflow-storage')
    dst_blob = dst_bucket.blob(streaming_filename)
    dst_blob.upload_from_filename(local_filename)

    os.remove(local_filename)
    return streaming_filename
