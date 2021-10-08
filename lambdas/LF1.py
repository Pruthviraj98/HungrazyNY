import math
import dateutil.parser
import datetime
import time
import os
import logging
import json
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']
    
def send_sqs_message(QueueURL, msg_body):
    """
    :param QueueName: String name of existing SQS queue
    :param msg_body: String message body
    :return: Dictionary containing information about the sent message. If
        error, returns None.
    """
    
    sqs = boto3.client('sqs')

    queue_url = QueueURL
    try:
        # Send message to SQS queue
        response = sqs.send_message(
            QueueUrl=queue_url,
            DelaySeconds=10,
            MessageAttributes={
                'cuisine': {
                    'DataType': 'String',
                    'StringValue': msg_body['cuisine']
                },
                'location': {
                    'DataType': 'String',
                    'StringValue': msg_body['location']
                },
                'phNo': {
                    'DataType': 'Number',
                    'StringValue': msg_body['phNo']
                },
                'time': {
                    'DataType': 'String',
                    'StringValue': msg_body['time']
                },
                'num_people': {
                    'DataType': 'Number',
                    'StringValue': msg_body['num_people']
                }
            },
            MessageBody=(
                'Information about the diner'
            )
        )
    
    except ClientError as e:
        logging.error(e) 
        return None
    
    return response
 
    
    
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
    
def build_validation_result(is_valid, violated_slot, message_content):
    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def validate_parameters(time_, cuisine, location, num_people, phone_number):
    
    # cuisine validation
    cuisine_types = ['chinese', 'indian', 'middleeastern', 'italian', 'mexican']
    if not cuisine:
        return build_validation_result(False, 'cuisine', 'What cuisine do you prefer?')
        
    elif cuisine.lower() not in cuisine_types:
        return build_validation_result(False, 'cuisine', 'We do not have any restaurant serving {}, would you like a different cuisine'.format(cuisine))
    
    # time validation
    if not time_:
        return build_validation_result(False, 'time', 'What time do you prefer?')
    
    # location validation
    if not location:
        return build_validation_result(False, 'location', 'Which city do you prefer?')

    # location validation
    if not num_people:
        return build_validation_result(False, 'num_people', 'How many of you are going?')
    
    if not phone_number:
        return build_validation_result(False, 'phNo', 'Please share your phone number')
    
    return build_validation_result(True, None, None)



def get_restaurants(intent_request):
    """
    Performs dialog management and fulfillment for asking details to get restaurant recommendations.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """
    
    source = intent_request['invocationSource']
    
    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)
        
        time_ = slots["time"]
        cuisine = slots["cuisine"]
        location = slots["location"]
        num_people = slots["num_people"]
        phone_number = slots["phNo"]
        
        slot_dict = {
            'time': time_,
            'cuisine': cuisine,
            'location': location,
            'num_people': num_people,
            'phNo': phone_number
        }
        
        validation_result = validate_parameters(time_, cuisine, location, num_people, phone_number)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                              intent_request['currentIntent']['name'],
                              slots,
                              validation_result['violatedSlot'],
                              validation_result['message'])


    res = send_sqs_message('https://sqs.us-east-1.amazonaws.com/680435484788/hungrazy', slot_dict)
    
    
    if res:
        response = {
                    "dialogAction":
                        {
                         "fulfillmentState":"Fulfilled",
                         "type":"Close",
                         "message":
                            {
                              "contentType":"PlainText",
                              "content": "Cool! we have received your request. You will soon have a message on your phone with recommendations enlisted! {},{},{},{},{}".format(
                                  time_, cuisine, location, num_people, phone_number),
                            }
                        }
        }
    else:
        response = {
                    "dialogAction":
                        {
                         "fulfillmentState":"Fulfilled",
                         "type":"Close",
                         "message":
                            {
                              "contentType":"PlainText",
                              "content": "We are experiencing problem. Please try after some time!",
                            }
                        }
                    }
    return response

def dispatch(event):
    logger.debug('dispatch userId={}, intentName={}'.format(event['userId'], event['currentIntent']['name']))
    intent_name = event['currentIntent']['name']
    if intent_name == 'diningsuggestion':
        return get_restaurants(event)
    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
