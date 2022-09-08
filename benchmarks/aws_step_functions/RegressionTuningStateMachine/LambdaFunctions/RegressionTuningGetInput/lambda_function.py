import json
import datetime

def lambda_handler(event, context):
    
    samplesNum = event['samplesNum']
    
    return {
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'samplesNum': samplesNum},
        })
    }