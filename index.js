var messages = [],
prevMessage = "", 
botName = 'Hungrazy',
var apigClient = apigClientFactory.newClient({
  region: 'us-east-1'
});

function chatbotAPI(message_payload) {
  apigClient.chatbotPost({}, message_payload)
      .then(function(response) {
        for(var i=0; i<response.data.messages.length; i++) {
          messages.push("<b>" + botName + ":</b> " + response.data.messages[i].unstructured.text);
        }
        for (var i = 1; i < 11; i++) {
        if (messages[messages.length - i])
          document.getElementById("chatlog" + i).innerHTML = messages[messages.length - i];
        }
      });
}


// for every new query entered, push the query into message and parse it and put the reply to messages as well
function newReply() {
  if (document.getElementById("chatbox").value != "") {
    prevMessage = document.getElementById("chatbox").value;
    document.getElementById("chatbox").value = "";
    messages.push("<b>"+"You: "+"</b>" +prevMessage);
    var message_payload = {
      'messages': [
        {
          "type":"string",
          "unstructured": {
            "id": "1",
            "text": prevMessage,
          }
        }
      ]
    }
    chatbotAPI(message_payload);
  }
}

// when enter is pressed, capture the current query and parse it
document.onkeypress = keyPress;
function keyPress(e) {
  var x = e || window.event;
  var key = (x.keyCode || x.which);
  if (key == 13 || key == 3) {
    newReply();
  }
}


//clear the input box when enter is pressed
function placeHolder() {
  document.getElementById("chatbox").placeholder = "";
}