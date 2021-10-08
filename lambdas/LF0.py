import json
import boto3
import datetime
def lambda_handler(event, context):
    message = event['messages']
    bot_response_message = "Please Try again!"
    
    if message is not None or len(message) > 0:
        data = message[0]['unstructured']['text']
        client = boto3.client('lex-runtime')
        bot_response = client.post_text(botName='HungrazyNY', botAlias='dining_bot', userId='test', inputText= data)
        
        bot_response_message = bot_response['message']
        
    response = {
        'messages': [
            {
                "type":"string",
                "unstructured": {
                    "id":"1",
                    "text": bot_response_message,
                    "timestamp": str(datetime.datetime.now().timestamp())
                }
            }
            ]
    }
    
    return response
