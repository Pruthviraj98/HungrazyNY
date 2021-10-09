import uuid
import datetime
import logging
import boto3
import json
from botocore.exceptions import ClientError
import requests
import decimal
from aws_requests_auth.aws_auth import AWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection
import os

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(0,len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        return str(obj)
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj
    
def get_sqs_data(queue_URL):
    sqs = boto3.client('sqs')
    queue_url = queue_URL
    
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'time', 'cuisine', 'location', 'num_people', 'phNo'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=0
        )

        # print(response['Messages'][0]['MessageAttributes'])
        messages = response['Messages'] if 'Messages' in response.keys() else []

        for message in messages:
            receiptHandle = message['ReceiptHandle']
            sqs.delete_message(QueueUrl=queue_URL, ReceiptHandle=receiptHandle)
        return messages
    
    except ClientError as e:
        logging.error(e) 
        return []
        
        
def compose_es_payload(msg_attributes, n):
    epoch = datetime.datetime.utcfromtimestamp(0)
    seed = (datetime.datetime.utcnow() - epoch).total_seconds() * 1000.0
    return {
        "query": {
            "function_score": {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"cuisine": msg_attributes['cuisine']['StringValue'].lower()}}
                        ]
                    }
                },
                "random_score": {"seed": str(seed)},
                "score_mode": "sum"
            }
        },
        "from": 0,
        "size": n
    }

def es_search(host, query):
    awsauth = AWSRequestsAuth(aws_access_key='AKIAZ43I5RB2F2QLHFOL',
                      aws_secret_access_key='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',
                      aws_host=host,
                      aws_region='us-east-1',
                      aws_service='es')
    
    # # use the requests connection_class and pass in our custom auth class
    esClient = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        use_ssl=True,
        http_auth=awsauth,
        verify_certs=True,
        connection_class=RequestsHttpConnection)
    
    es_result=esClient.search(index="restaurants", body=query)    # response=es.get()
    # print(es_result)
    return es_result
    
    
def get_dynamo_data(dynno, table, key):
    response = table.get_item(Key={'id':key}, TableName='yelp-restaurants')
    
    response = replace_decimals(response)
    name = response['Item']['name']
    address_list = response['Item']['address']
    return '{}, {}'.format(name, address_list)

def lambda_handler(event, context):
    
    # Create SQS client
    sqs = boto3.client('sqs')

    es_host = 'search-hungrazy-sii2r2352getluqu2hlz2qptzi.us-east-1.es.amazonaws.com'
    table_name = 'yelp-restaurants'
    
    messages = get_sqs_data('https://sqs.us-east-1.amazonaws.com/680435484788/hungrazy')
    
    logging.info(messages)
        
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    

    for message in messages:
        logging.info(message)
        msg_attributes=message['MessageAttributes']
        query = {"query": {"match": {"cuisine": msg_attributes["cuisine"]["StringValue"]}}}
        es_search_result = es_search(es_host, query)
        print(es_search_result, "THISIISSS ITTTTTTT")
        number_of_records_found = int(es_search_result["hits"]["total"]["value"])
        # print(es_result)
        hits = es_search_result['hits']['hits']
        suggested_restaurants = []
        for hit in hits:
            id = hit['_source']['id']
            suggested_restaurant = get_dynamo_data(dynamodb, table, id)
            suggested_restaurants.append(suggested_restaurant)
        print(suggested_restaurants)
        
        text = "Hello! Here are the "+msg_attributes['cuisine']['StringValue']+ " suggestions for "+msg_attributes['num_people']['StringValue']+" people at "+ msg_attributes['time']['StringValue']+" "
        for i,rest in enumerate(suggested_restaurants):
	        text += "(" + str(i+1) + ")" + rest
        
        print(text)
        # logging.info(text)
        
        phone_number = msg_attributes['phNo']
        # arn="arn:aws:sns:us-east-1:680435484788:hungrazyChatBotSNS"
        sns_client = boto3.client('sns' , 'us-east-1')
        # status = sns_client.publish(
        #     Message=text, 
        #     MessageStructure='string',
        #     PhoneNumber = phone_number)
            
        response = sns_client.publish(
            TopicArn="arn:aws:sns:us-east-1:680435484788:hungrazy",
            Message=text
        )

        print(response, "THIS SHIT IS COMPLETE")
        
    # Create SQS client
