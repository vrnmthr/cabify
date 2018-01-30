import os
import sys
from datetime import datetime
import logging
import requests
import json
from flask import Flask, request
from multiprocessing import Process
import time

app = Flask(__name__)
data = {
    "routing": 0
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

def run_loop():
    while True:
    print "I ran"
    time.sleep(5)

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

                    if message_text == "loop":
                        p = Process(target=run_loop)
                        p.start()
                    else:
                        try:
                            dept, code, crn = message_text.split(" ")
                            data = post_course(dept, code, crn)
                            parsed = parse_JSON(data)
                            seats = int(parsed["avail"])
                            send_message(sender_id, "There are {rem} seats left in {d}{cc}".format(rem=seats,d=dept,cc=code))
                            if seats <= 0:
                                send_message(sender_id, "Should I message you when one opens up? (y/n)")
                        except ValueError, e:
                            logging.exception("error occurred")
                            send_message(sender_id, "I didn't get that. Try typing [course] [code] [CRN]")
                            send_message(sender_id, "CSCI 0180 25748 should work")


                    """
                    split = message_text.split(" ")
                    if len(split) < 3:
                        send_message(sender_id, "I didn't get that. Try typing [course] [code] [CRN]")
                        send_message(sender_id, "CSCI 0180 25748 should work")
                    else:


                    try:
                        send_message(sender_id, "hi")
                        dept, code, crn = message_text.split(" ")
                        dept = dept.upper()
                        coursesearch = "%20".join([dept, code])
                        send_message(sender_id, coursesearch)
                        send_message(sender_id, crn)
                        res = post_course(coursesearch, crn)
                        parsed = parse_JSON(res)
                        rem = parsed["avail"]
                        formatted = "There are " + str(rem) + " seats available in CSCI 1550"
                        send_message(sender_id, formatted)

                    except Exception, e:
                        send_message(sender_id, "failed" + str(e))
                        logging.exception("error occurred")
                        log("error occurred")

                    #course, crn = message_text.split(" ")
                    #send_message(sender_id, "{course} seems to be free right now!".format(course=course))
                    """

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

def find_class_info():

    cookies = {
        '_ga': 'GA1.2.1179830460.1510250977',
        '__utma': '117564634.1179830460.1510250977.1511049538.1512078967.2',
        '__utmz': '117564634.1512078967.2.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
    }

    headers = {
        'Origin': 'https://cab.brown.edu',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://cab.brown.edu/',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    params = (
        ('output', 'json'),
        ('page', 'asoc.rjs'),
        ('route', 'course'),
    )

    data = [
      ('term', '201720'),
      ('course', 'CSCI%201550'),
      ('id', '25756'),
      ('instId', ''),
    ]

    res = requests.post('https://cab.brown.edu/asoc-api/', headers=headers, params=params, cookies=cookies, data=data)
    print "content: "
    print res.content
    print res.status_code
    parsed = res.json()
    print "attempting to interpret parsing: "
    #print typeof(parsed)
    print parsed["sections"][0]["avail"]
    return res.json()

def post_course(dept, code, crn):

    dept = dept.upper()
    encoded = "%20".join([dept, code])

    cookies = {
        '_ga': 'GA1.2.1179830460.1510250977',
        '__utma': '117564634.1179830460.1510250977.1511049538.1512078967.2',
        '__utmz': '117564634.1512078967.2.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided)',
    }

    headers = {
        'Origin': 'https://cab.brown.edu',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://cab.brown.edu/',
        'X-Requested-With': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    params = (
        ('output', 'json'),
        ('page', 'asoc.rjs'),
        ('route', 'course'),
    )

    data = [
      ('term', '201720'),
      # needs to parse spaces to remove %20
      #('course', 'CSCI%201550'),
      ('course', encoded),
      #('id', '25756'),
      ('id', crn),
      ('instId', ''),
    ]

    res = requests.post('https://cab.brown.edu/asoc-api/', headers=headers, params=params, cookies=cookies, data=data)
    print "content: "
    print res.content
    print "status code: " + str(res.status_code)
    return res

def parse_JSON(res):
    """
    Returns a dict containing JSON information for the class
    """
    parsed = res.json()
    print "parsed: "
    print parsed
    return parsed["sections"][0]

def send_message(recipient_id, message_text):

    #log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

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
