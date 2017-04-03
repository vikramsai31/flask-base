from flask import Flask, request, json, jsonify
from datetime import datetime, time
import requests
import logging
import time
import uuid
import json
import config
from service import Service
logging.basicConfig(level=logging.INFO)
logging = logging.getLogger(__name__)


app = Flask(__name__)
app.config.from_pyfile('flaskapp.cfg')

ACCESS_TOKEN = "EAAHGiGtsLMgBABF3Uz9NWoEqiMcZA1NS0RwK81qM2L3mvZBqeSfWln1qugkk10ITgiCKEHVu1yksWBwFTEckRuijQKOAZAC2ZBa5qNufRUhRMQBc7Ks1Rz4khsv6pWwrwCKmtrrxXcQzdvYX6X88fLc3ZAVUK2sVpziQso4JGO0IYLkdd04ZAM"
VERIFY_TOKEN = "Iam_vikram"
GREETING_RESP = ["Hi {{user_full_name}}"]
GREETING_KEYWORDS = ("hello", "hey", "hi", "greetings", "sup", "what's up", "yo",)
QUESTIONS = ["Lets start with make,model & year of your car", ]
QUICK_ANS = ["It's nice one", "Great", "Ok"]
resp = None
customer_list = {}
db = Service()
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
	data = request.get_json()
	logging.info(data)
	if data["object"] == "page":
		for entry in data["entry"]:   
			for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]
                recipient_id = messaging_event["recipient"]["id"]
                user_dict = {'sender_id':sender_id, 'recipient_id':recipient_id, 'counter':0}
                
                 if db.check_active_session(user_dict) == True:
                      current_state = db.get_current_state(user_dict)
                 if db.check_active_session(user_dict) == False:
                     user_dict['status'] = 'NEW'
                     db.record_session(user_dict)
                     current_state = db.get_current_state(user_dict)
                 if messaging_event.get("postback"):
                     if messaging_event['postback']['payload'] == 'DEVELOPER_DEFINED_PAYLOAD_ABOUT_US':
                         user_dict['status'] = 'ABOUT US'
                         db.record_session(user_dict)
                         about_us = db.get_information(recipient_id)
                         send_message(sender_id, "Here you go !!")
                         send_message(sender_id, about_us)
                         time.sleep(2)
                         send_message(sender_id, "I'll save you sometime how about an service appointment")
                         send_custom_message(sender_id, "I\'ll make it easier for you , just opt for one below", [{'type':'postback', 'title':'Yes, Appointment', 'payload':'APPOINTMENT_YES'}, {'type':'postback', 'title':'No, Appointment', 'payload':'APPOINTMENT_NO'}])
                    if messaging_event['postback']['payload'] in ('DEVELOPER_DEFINED_PAYLOAD_APPOINTMENT', 'APPOINTMENT_YES'):
                        user_dict['status'] = messaging_event['postback']['payload']
                        db.record_session(user_dict)
                        send_message(sender_id, 'Great!!, lets get started')
                        send_quick_reply_message(sender_id, 'Pick a day', db.get_appt_day())
                    if messaging_event['postback']['payload'] == "APPOINTMENT_NO":
                        user_dict['status'] = "APPOINTMENT_NO"
                        db.record_session(user_dict)
                        user_dict['status'] = "COMPLETE"
                        db.record_session(user_dict)
                        send_message(sender_id, "Thanks for chatting, I'll be around if you need me")
                    if messaging_event['postback']['payload'] == "DEVELOPER_DEFINED_PAYLOAD_SERVICE":
                        user_dict['status'] = 'SERVICE'
                        db.record_session(user_dict)
                        send_message(sender_id, 'Great!!, lets get started')
                        send_quick_reply_message(sender_id, 'Tell me what you looking for', db.get_service_category(recipient_id))
                        
                 if messaging_event.get("message"):
                     if "attachment" in  messaging_event["message"]:
                         resp = send_image(sender_id)
                     if messaging_event["message"]["text"]: 
                         message_text = messaging_event["message"]["text"].lower()
                         if check_for_greetings(message_text) is True and current_state == 'NEW':
                             respond(sender_id, message_text)
                         if current_state == "APPT_PHONE":
                             if valid_phone_number(message_text) == True:
                                 send_message(sender_id, "Awesome!, Someone from shop will call you and confirm the appointment")
                                 send_message(sender_id, "Thanks for chatting, I'll be around if you need me")
                                 user_dict['status'] = "COMPLETE"
                                 user_dict['phone_number'] = messaging_event["message"]["text"]
                                 db.record_session(user_dict)
                                 db.update_phone_number(user_dict)
                            else:
                                send_message(sender_id, "Please make sure the phone number is in xxx-xxx-xxxx format")
                                
                     if "quick_reply" in messaging_event["message"]:
                         if messaging_event["message"]["quick_reply"]["payload"] == "DEVELOPER_DEFINED_CATEGORY":
                             send_quick_reply_message(sender_id, 'Got it what service type you looking for', db.get_service_list(recipient_id, messaging_event["message"]["text"]))
                             if db.check_appt_today(sender_id, recipient_id) == True:
                                 user_dict['service_category'] = messaging_event["message"]["text"]
                                 db.update_service_category(user_dict)
                        
                         if messaging_event["message"]["quick_reply"]["payload"] == "DEVELOPER_DEFINED_SERVICE":
                             if current_state in ('DEVELOPER_DEFINED_PAYLOAD_APPOINTMENT', 'APPOINTMENT_YES'):
                                 user_dict['status'] = "APPT_PHONE"
                                 db.record_session(user_dict)
                                 send_message(sender_id, "Please provide your phone number in followig format xxx-xxx-xxxx")
                             if db.check_appt_today(sender_id, recipient_id) == True:
                                 user_dict['service_type'] = messaging_event["message"]["text"]
                                 db.update_service_type(user_dict)
                             if current_state == ('SERVICE'):
                                 send_message(sender_id, "Would you like me to schedule an appointment")
                                 send_custom_message(sender_id, "I\'ll make it easier for you , just opt for one below", [{'type':'postback', 'title':'Yes, Appointment', 'payload':'APPOINTMENT_YES'}, {'type':'postback', 'title':'No, Appointment', 'payload':'APPOINTMENT_NO'}])
                        
                         if messaging_event["message"]["quick_reply"]["payload"] == "DEVELOPER_DEFINED_APPT_DAY":
                             
                             user_dict['name'] = get_name(sender_id)
                             user_dict['day_of_appt'] = messaging_event["message"]["text"]
                             if db.check_if_appt_exists(sender_id, messaging_event["message"]["text"]) == False:
                                 db.insert_appt(user_dict)
                                 send_quick_reply_message(sender_id, 'Pick a service window', db.get_time_slot())
                             else:
                                 send_quick_reply_message(sender_id, 'Looks like you already have an appointment, pick another day', db.get_appt_day())
                         if messaging_event["message"]["quick_reply"]["payload"] == "DEVELOPER_DEFINED_TIME_SLOT":
                             send_quick_reply_message(sender_id, 'Tell me what you looking for', db.get_service_category(recipient_id))
                             user_dict['day_of_appt'] = messaging_event["message"]["text"]
                             db.update_appt_window(user_dict)
                                                                             
	return "ok", 200


def check_for_greetings(message_text):
     if len(message_text) < 10 and message_text.lower() in GREETING_KEYWORDS:
         return True
     

def initial_message(recipient_id, message_text):
	params = {
        "access_token": ACCESS_TOKEN
        }
        headers = {
        "Content-Type": "application/json"
        }
	data = json.dumps({
        "recipient": {"id": recipient_id
        },
         "message":{
        "attachment":{
        "type":"template",
        "payload":{
        "template_type":"button",
         "text":"Welcome!!, lets get you started",
         "buttons":[
              {
                "type":"postback",
                "title":"About us",
                "payload":"DEVELOPER_DEFINED_PAYLOAD_ABOUT_US"
              }, {
                "type":"postback",
                "title":"Book An appointment",
                "payload":"DEVELOPER_DEFINED_PAYLOAD_APPOINTMENT"
              },
            {
                "type":"postback",
                "title":"Ask For Service",
                "payload":"DEVELOPER_DEFINED_PAYLOAD_SERVICE"
              }              
            ]      
          }
        }
        }
        })
        resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        logging.info(resp.content)
        if resp.status_code != 200:
    	    logging.info(resp.status_code)
    	    logging.info(resp.text)


def send_initial_message(recipient_id):
	for greeting in GREETING_RESP:
		initial_message(recipient_id, greeting)
		time.sleep(0.1)
	
	return "ok", 200

def send_message(recipient_id, message_text):
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
            "text": message_text,
        }
        })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    logging.info(resp.content)
    if resp.status_code != 200:
        logging.info(resp.status_code)
        logging.info(resp.text)

def send_custom_message(recipient_id, message_text, postback_dict):
    params = {
        "access_token": ACCESS_TOKEN
        }
    headers = {
        "Content-Type": "application/json"
        }

    data = json.dumps({
         "recipient": {"id": recipient_id
        },
        "message":{
            "attachment":{
            "type":"template",
        "payload":{
        "template_type":"button",
        "text": message_text,
        "buttons":postback_dict
         }
        }
        }
        })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    return data
    logging.info(resp.content)
    if resp.status_code != 200:
        logging.info(resp.status_code)
        logging.info(resp.text)

def send_quick_reply_message(recipient_id, message_text, user_dict):
    params = {
        "access_token": ACCESS_TOKEN
        }
    headers = {
        "Content-Type": "application/json"
        }

    data = json.dumps({
         "recipient": {"id": recipient_id
        },
        "message":{
         "text":message_text,
         "quick_replies": user_dict
        }
        })
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if resp.status_code != 200:
        logging.info(resp.status_code)
        logging.info(resp.text)


def respond(recipient_id, message_text):
    try:
        send_initial_message(recipient_id)
        return 'ok'
    except:
        print("****Error on respond****")


def get_name(sender_id):
    try:
        resp = "https://graph.facebook.com/v2.6/%s?fields=first_name,last_name&access_token=%s" % (sender_id, ACCESS_TOKEN)
        data = requests.get(resp).json()
        return data["last_name"] + " " + data["first_name"]    
    except:
        logging.info(resp)
        return None

def valid_phone_number(phone_number):
    if len(phone_number) != 12:
        return False
    for i in range(1, 12):
        if i in (3, 7):
            if phone_number[i] != '-':
                return False
        elif  not phone_number[i].isdigit():
            return False
    return True






if __name__ == '__main__':
    # app.run(debug=True)

    # postback=[{'type':'postback','title':'Yes, Appointment','payload':'yes'},{'type':'postback','title':'No, Appointment','payload':'no'}]
    x = get_name(683561181769029)
    print x
    
		













