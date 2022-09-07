import json
import datetime

def lambda_handler(event, context):
    
    try:
        input_text = event['input']
        print("Retrieved: "+str(input_text))
    except:
        print("Could not read input value. Defaulting to 'Hello World!'")
        input_text = "Hello World!"
    
    input_text = event['input']
    
    return {
        'statusCode': 200,
        'timestamp': datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
        'body': json.dumps({
            'data': {'input': input_text},
        })
    }
