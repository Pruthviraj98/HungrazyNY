import requests
import simplejson as json
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

def get_business_attributes(business, location, cuisine_type):
    attributes_dictionary={}
    attributes_dictionary['id']=business['id']
    attributes_dictionary['location']=location
    attributes_dictionary['cuisine_type']=cuisine_type
    attributes_dictionary['name']=business['name']
    attributes_dictionary['url']=business['url']
    if not check_if_none(business.get("rating",None)):
        attributes_dictionary["rating"] = Decimal(business["rating"])
    if not check_if_none(business.get("phone",None)):
        attributes_dictionary["contact"] = business["phone"]
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
    businesses=[]
    for offset in range(0, 5000, 50):
        parameters={'term':"Restaurants", 'location':'New York City', 'categories':cuisine_type, 'limit':50, 'offset':offset}
        headers= {"Authorization": "Bearer " + api_key}    
        response= requests.get(url=api, headers=headers, params=parameters).json()
        if 'businesses' in response:
            response_businesses=response["businesses"]
            for business in response_businesses:
                business_attributes=get_business_attributes(business, location, cuisine_type)
                businesses.append(business_attributes)
    return businesses

def put_data_to_open_search():
    dynamoDB=boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id='AKIAZ43I5RB2KS62WRFI', aws_secret_access_key='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')
    table=dynamoDB.Table('yelp-restaurants')   
    host='search-hungrazy-sii2r2352getluqu2hlz2qptzi.us-east-1.es.amazonaws.com'
    credentials = boto3.Session(region_name='us-east-1', aws_access_key_id='AKIAZ43I5RB2KS62WRFI', aws_secret_access_key='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').get_credentials()
    auth=AWS4Auth(credentials.access_key, credentials.secret_key, 'us-east-1', 'es')
    es=Elasticsearch(
        hosts=[{'host':host, 'port':443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    table_details=table.scan()
    items=table_details['Items']
    for item in items:
        document={
            "id":item['id'],
            'cuisine':item['cuisine_type']
        }
        es.index(index="restaurants", doc_type="restaurant", id=item['id'], body=document)
        

def put_data_to_database(restaurants):
    dynamoDB=boto3.resource('dynamodb', region_name='us-east-1', aws_access_key_id='AKIAZ43I5RB2KS62WRFI', aws_secret_access_key='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')
    table=dynamoDB.Table('yelp-restaurants')
    total_count=0
    for restaurant_dictionary in restaurants:
        try:
            table.put_item(Item=restaurant_dictionary)
            total_count+=1
        except:
            pass
    print('Total restaurants inserted : '+ str(total_count))

if __name__=='__main__':
    api_key = 'UGfyjJYtEPxERNAf2oXPbzMImppLy1araZXiLxuBgAGPFWyrvAbOjgDJdC9SyqotRvy8jYkp0lUMyIvLMTT3Yo4LzTe009D1VGW3FJB3ZZlwQUFghD8_0OBePc9XYXYx'
    api='https://api.yelp.com/v3/businesses/search'
    service='es'
    response_restaurants=scrape_yelp_data(api, api_key, "indpak", "manhattan")+scrape_yelp_data(api, api_key, "italian", "manhattan")+scrape_yelp_data(api, api_key, "mexican", "manhattan")+scrape_yelp_data(api, api_key, "chinese", "manhattan")+scrape_yelp_data(api, api_key, "mideastern", "manhattan")
    put_data_to_database(response_restaurants)
    put_data_to_open_search()
    with open('data/all_restaurants.json', 'w') as f:
        temp=json.dumps(response_restaurants, indent=4, separators=(',', ':'))
        f.write(temp) 