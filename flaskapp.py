from flask import Flask, request,json, jsonify
import requests
import logging
import time
import config
import json
import nltk
import service
from textblob import TextBlob
logging.basicConfig(level=logging.INFO)
logging = logging.getLogger(__name__)
#Lets start with make,model & year of the car
#reply: its a nice car
#could you also provide me the mileage and service you looking for

app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')



customer_list = {}
db = Autoservice()

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Connected", 200

@app.route('/', methods=['POST'])

def handle_incoming_messages():
    user_dict = {}
    try:
        data = request.get_json()
        logging.info(data)
        if data["object"] == "page":
            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    if messaging_event.get("message"):
                        sender_id = messaging_event["sender"]["id"]
                        recipient_id = messaging_event["recipient"]["id"]
                        #check for attachments and reply with attachments
                        if "attachment" in  messaging_event["message"]:
                        	resp=send_image(sender_id)
                        if messaging_event["message"]["text"] :
                            user_dict[:sender_id]=sender_id
                            user_dict[:recipient_id]=recipient_id
                            user_dict[:status]='N'
                            user_dict[:seq_id]=messaging_event["message"]["seq"]
                            #db.record_session(user_dict)
                            message_text = messaging_event["message"]["text"]
                        	if check_for_greetings(message_text) is True:
                        		resp=respond(sender_id ,message_text)	
                                user_dict[:status]='G'
                                #db.record_session(user_dict)
                        	if messaging_event["message"]["text"] == "Got it!!" and messaging_event["message"]["quick_reply"]["payload"] == "DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GOTIT":
                        		gather_information(sender_id,messaging_event["message"]["seq"])
                                user_dict[:status]='ACK'
                                #db.record_session(user_dict)
                        elif messaging_event["message"]["text"] and db.check_active_session(sender_id) is False:
                        	gather_information(sender_id,messaging_event["message"]["seq"],messaging_event["message"]["text"])
                        else:
                            user_dict[:status]='E'
                            #db.record_session(user_dict)
                        	resp=send_message(sender_id,"I didn't get you, lets try again!!")
                                                                                  
except:
        logging.info(resp)
    return "ok", 200

def check_for_greetings(message_text):
	if len(message_text) < 10 and message_text.lower() in GREETING_KEYWORDS:
		return True



def send_message(recipient_id,message_text):
	params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
	data = json.dumps({
        "recipient": {"id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    logging.info(resp.content)
    if resp.status_code != 200:
    	logging.info(resp.status_code)
    	logging.info(resp.text)


def send_initial_message(recipient_id):
	for greeting in GREETING_RESP:
		send_message(recipient_id,greeting)
		time.sleep(0.1)
	

def respond(recipient_id ):
		send_initial_message(recipient_id)
		resp = send_ack(recipient_id)
	    logging.info(resp)
	return 'ok'

def send_ack(recipient_id):
	params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
	data = json.dumps({
        "recipient": {"id": recipient_id
        },
        "message": {
            "text": "All Clear!!",
            "quick_replies":[
            {
            "content_type":"text",
            "title":"Got it!!",
            "payload":"DEVELOPER_DEFINED_PAYLOAD_FOR_PICKING_GOTIT",
            "image_url":"https://assets-cdn.github.com/images/icons/emoji/unicode/1f44d.png?v7"
            }
            ]
        }
    })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    logging.info(resp.content)
    return resp

def send_image(recipient_id):
	params = {
        "access_token": ACCESS_TOKEN
    }
    headers = {
        "Content-Type": "application/json"
    }
	data = json.dumps({
        "recipient": {"id": recipient_id
        },
        "message": {
            "attachment": {
            "type":"image",
            "payload":{
            "url":"https://scontent.xx.fbcdn.net/v/t39.1997-6/851557_369239266556155_759568595_n.png?_nc_ad=z-m&oh=65f8806bcfe45834eb50b60f51cb352d&oe=596142DC"
            }
            }
            }
    })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    logging.info(resp.content)
    return resp

def gather_information(recipient_id,sequence,message_text):
 """lets begin gathering information,keep track of sequence"""
 	if  not customer_list:
 		for question in QUESTIONS:
 			send_message(recipient_id,question)
 			customer_list.update({'seq': sequence, 'user_id' : recipient_id})
 			print customer_list
 	else:
        #check for nouns
        words= get_keywords(message_text)
        print words
 		send_message(recipient_id,"I'm getting there")
    return "ok"


def get_keywords(sentence):
    good_tags=set(['JJ','JJR','JJS','NN','NNP','NNS','NNPS','CD'])
    parsed = TextBlob(sentence)
    token = parsed.pos_tags
    keywords =[]
    for word,tag in token:
        if tag in good_tags:
            keywords.append(word)
    return keywords


        

if __name__ == '__main__':
    app.run(debug=True)
    #x = respond("1270445009706340","hello")
    

		












