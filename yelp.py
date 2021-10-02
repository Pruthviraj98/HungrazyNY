import requests
import json
import os
from decimal import Decimal
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3

def check_if_none(val):
    try:
        if val is None or len(str(val)) == 0:
            return True
        return False
    except:
        return True

def get_business_attributes(business, location, cuisine_type, cuisine_name):
    attributes_dictionary={}
    attributes_dictionary['id']=business['id']
    attributes_dictionary['location']=location
    attributes_dictionary['cuisine_type']=cuisine_type
    attributes_dictionary['name']=business['name']
    attributes_dictionary['url']=business['url']
    if not check_if_none(business.get("rating",None)):
        attributes_dictionary["rating"] = Decimal(business["rating"])
    if not check_if_none(business.get("phone",None)):
        attributes_dictionary["contact"] = business["contact"]
    if not check_if_none(business.get("review_count",None)):
        attributes_dictionary["review_count"] = business["review_count"]
    if not check_if_none(business.get("price",None)):
        attributes_dictionary["price"] = business["price"]
    if business.get('location', None) is not None:
        temp=""
        for line in business['location']['display_address']:
            temp+=line
        attributes_dictionary['address']=temp

    return attributes_dictionary


def scrape_yelp_data(api, api_key, cuisine_type, location):
    query= "?location={}".format(location)+"&categories={}".format(cuisine_type)+"&limit=50"
    yelp_api=api+query
    headers= {"Authorization": "Bearer " + api_key}
    #get all the responses
    response= requests.get(yelp_api, headers=headers).json()
    offset=0
    total_responses=response['total']
    businesses=[]
    #loop untill the you reach end of all the responses
    while(total_responses>=0):
        #but json has pages. So, loop through all the pages untill its none
        if response.get("businesses", None) is not None:
            response_businesses=response["businesses"]
            #loop through businesses in the current page
            responses_in_current_page=len(response_businesses)
            #for every business in the current page, get the attribute and put it in the business array
            for business in response_businesses:
                business_attributes=get_business_attributes(business, location, cuisine_type)
                businesses.append(business_attributes)
            #Decreased total responses by total responses parsed.
            total_responses-=responses_in_current_page
            #And increase the offset by number of businesses parsed
            offset+=responses_in_current_page
            #call the next page like this
            response=requests.get(yelp_api+query+str(offset), headers=headers).json()
        else:
            break
    return businesses

def put_data_to_open_search(response_restaurants, esClient):
    db = boto3.resource('dynamodb')
    table=db.Table('yelp-restaurants')
    total_restaurants=len(response_restaurants)
    batch_size=total_restaurants//20
    remaining_batches = batch_size
    start_index = -batch_size

    while remaining_batches!=0 :
        start_index = start_index+batch_size
        with table.batch_writer() as batch:
            for restaurant in response_restaurants[start_index:start_index+batch_size]:
                batch.put_item(Item=restaurant)
        for restaurant in response_restaurants[start_index:start_index + batch_size]:
            esClient.index(index='restaurant', doc_type='doc', body={
                "id" : restaurant["id"],
                "cuisine" : restaurant["cuisine_type"],
            })
        remaining_batches = remaining_batches-1


if __name__=='__main__':
    api_key = 'UGfyjJYtEPxERNAf2oXPbzMImppLy1araZXiLxuBgAGPFWyrvAbOjgDJdC9SyqotRvy8jYkp0lUMyIvLMTT3Yo4LzTe009D1VGW3FJB3ZZlwQUFghD8_0OBePc9XYXYx'
    api='https://api.yelp.com/v3/businesses/search'
    service='es'
    credentials = boto3.Session(region_name='us-east-1', aws_access_key_id='', aws_secret_access_key='').get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', service)
    response_restaurants=scrape_yelp_data(api, api_key, "indpak", "manhattan")+scrape_yelp_data(api, api_key, "italian", "manhattan")+scrape_yelp_data(api, api_key, "mexican", "manhattan")+scrape_yelp_data(api, api_key, "chinese", "manhattan")+scrape_yelp_data(api, api_key, "mideastern", "manhattan")
    esClient = Elasticsearch(
        hosts=[{'host': "search-restaurants-dkzrlqqt4trhmdu5ujg3icvjba.us-east-1.es.amazonaws.com",'port':443}],
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        http_auth=awsauth
        )
    put_data_to_open_search(response_restaurants, esClient)
