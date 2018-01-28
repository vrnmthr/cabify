import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

app = Flask(__name__)
data = {
    "data["routing"]": 0
}

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"].lower()  # the message's text

                    if data["routing"] < 2:
                        # has asked about notification for a class
                        if data["routing"] <= 1.1:
                            # needs to say exact name
                            send_message(sender_id, "I need the CRN too")
                            data["routing"] = 1.2
                        elif data["routing"] <= 1.2:
                            # has just submitted CRN
                            send_message(sender_id, "Thanks - lemme check on that for you.")
                            send_message(sender_id, "I've processed your request. You'll be hearing from me soon :)")
                            data["routing"] = 1.3
                        else:
                            #default
                            send_message(sender_id, "I didn't get that.")
                            data["routing"] = 0
                    else:
                        if("can you notify me when a class becomes open" in message_text):
                            send_message(sender_id, "Sure! Tell me the exact name of the class.")
                            data["routing"] = 1
                        elif("what can you do" in message_text):
                            send_message(sender_id, "try asking: can you notify me when a class becomes open?")
                            data["routing"] = 0
                        else:
                            send_message(sender_id, "I didn't get that. Trying asking me what I can do.")
                            data["routing"] = 0


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
