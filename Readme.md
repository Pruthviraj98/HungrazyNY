# Hungrazy - A Dining Concierge Chatbot
Customer Service is a core service for a lot of businesses around the world and it is getting disrupted at the moment by Natural Language Processing-powered applications. Hungrazy is a server-less, microservice-driven web application specifically, a Dining Concierge chat bot that sends you restaurant suggestions given a set of preferences that you provide the chat bot with through conversation.

## Architechture diagram
![Alt text](https://github.com/Pruthviraj98/HungrazyNY/blob/main/Assignment%201%20architecture%20diagram.png?raw=true)

## <b>Components</b>
<ul>
  <li> <h4> S3 Bucket </h4> </li> Used to deploy the front-end starter application to interface with the chatbot
  <li> <h4> API Gateway </h4> </li> API Gateway handles all the tasks involved in accepting and processing up to hundreds of thousands of concurrent API calls, including traffic management, CORS support, authorization and access control,
  <li> <h4> Amazon Lex </h4> </li> Amazon Lex is a web service that allows customers to include conversational interfaces for voice and text in the software applications they are developing.
  <li> <h4> Lambda Function 0 (LF0) </h4> </li> Implemented LF0 to facilitate chat operation using request/response model (interfaces) specified in the API  
  <li> <h4> Lambda Function 1 (LF1) </h4> </li> Used LF1 as a code hook for Lex to manipulate and validate parameters as well as format the bot’s responses, which essentially entails the invocation of Lambda before Lex responds to any requests.  
  <li> <h4> Lambda Function 2 (LF2) </h4> </li> Developed LF2 to perform Open search on the data to get the top 5 results corresponding to the user's query and fetch the details from DynamoDB. The recommendations are sent to the users via email using Amazon SNS service.
  <li> <h4> SQS </h4> </li> Used to collect the information provided by the user and to an SQS queue 
  <li> <h4> DynamoDB </h4> Unstructed Database used to store the restaurant details scraped from Yelp </li> <p> </p>
  <li> <h4> Elastic Search/Open search </h4> Used to store the indices and cuisines of the data </li><p></p>
  <li> <h4> SNS </h4> </li> Used to notify the users with an email containing the top 5 restaurant recommendations
</ul>  

## Demo / Output / Screenshots / Results

