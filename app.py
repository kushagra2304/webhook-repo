from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

#MongoDB setup
MONGO_URI = "mongodb+srv://kush123:kush123@cluster0.8bvqrjj.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.github_events      
events_collection = db.events 

#Timestamp
def format_timestamp():
    return datetime.utcnow().isoformat()

#webhook endpoint
@app.route("/webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    payload = request.json
    normalized = None
   #push request
    if event_type == "push":
        normalized = {
            "event_type": "push",
            "author": payload["pusher"]["name"],
            "from_branch": None,
            "to_branch": payload["ref"].split("/")[-1],
            "timestamp": format_timestamp()
        }

    # pull request and merge request
    elif event_type == "pull_request":
        pr = payload["pull_request"]
        if payload["action"] == "closed" and pr["merged"]:
            normalized = {
                "event_type": "merge",
                "author": pr["merged_by"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": format_timestamp()
            }
        else:
            normalized = {
                "event_type": "pull_request",
                "author": pr["user"]["login"],
                "from_branch": pr["head"]["ref"],
                "to_branch": pr["base"]["ref"],
                "timestamp": format_timestamp()
            }
    if normalized:
        events_collection.insert_one(normalized)
        print("Stored event:", normalized)
    else:
        print("Event ignored:", event_type)

    return jsonify({"status": "ok"}), 200

# UI endpoint
@app.route("/events", methods=["GET"])
def get_events():
    events_cursor = events_collection.find().sort("timestamp", -1).limit(20) #latest 20 events only
    events = []
    for e in events_cursor:
        e["_id"] = str(e["_id"])  
        events.append(e)
    return jsonify(events), 200

@app.route("/")
def home():
    return "server is running!"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
