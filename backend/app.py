from flask import Flask, request,jsonify, render_template
from flask_cors import CORS # turns off restriction blocking webpage from talking to webpage
from dotenv import load_dotenv
import requests
import sqlite3
import os

load_dotenv() #load .env for api key :>

app = Flask(__name__) 
CORS(app)
API_KEY = os.getenv("YOUTUBE_API_KEY")

def init_db():
    conn = sqlite3.connect("videos.db") #connects to database
    c = conn.cursor() #cursor runs commands inside the database
    c.execute(""" 
        CREATE TABLE IF NOT EXISTS videos(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        video_id TEXT,
        title TEXT,
        channel TEXT,
        duration TEXT,
        category TEXT,
        seconds_watched INTEGER DEFAULT 0,
        watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        """) #triple quotes for mult line string 
    conn.commit()
    conn.close()

@app.route("/track", methods=["POST"]) #runs when someone sends a req to /track, sends data
def track():
    data = request.json
    print("recieved data", data)
    video_id = data["video_id"]
    seconds_watched = data.get("secondsWatched", 0)
    print("recieved video with watch time", video_id, seconds_watched)
    
    if not video_id:
        return jsonify({"status": "ignored"})
    
    existing = sqlite3.connect("videos.db")
    c = existing.cursor()
    c.execute("SELECT id, seconds_watched FROM videos WHERE video_id = ? ORDER BY watched_at DESC LIMIT 1", (video_id,))
    row = c.fetchone()
    
    if row and seconds_watched > 0:
        c.execute("UPDATE videos SET seconds_watched = seconds_watched + ? WHERE id = ?", (seconds_watched, row[0]))
        existing.commit()
        existing.close()
        return jsonify({"status": "updated"})
    existing.close()
       
    info = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "id": video_id,
            "part": "snippet,contentDetails",
            "key": API_KEY
        }
    ).json()
    

    item = info["items"][0]
    title = item["snippet"]["title"]
    channel = item["snippet"]["channelTitle"]
    duration = item["contentDetails"]["duration"]
    category = item["snippet"]["categoryId"]

    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("INSERT INTO videos (video_id, title, channel, duration, category, seconds_watched) VALUES (?,?,? ,?,?,?)",
    (video_id, title, channel, duration, category, seconds_watched))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/videos", methods=["GET"]) #get data
def get_videos():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("SELECT video_id, title, channel, duration, category, seconds_watched, watched_at FROM videos ORDER BY watched_at DESC") #fetch videos from db, ordered by descending watch time
    rows = c.fetchall()
    conn.close()

    videos = []
    for row in rows: # creates dictionary
        videos.append({
            "video_id": row[0],
            "title": row[1],
            "channel": row[2],
            "duration": row[3],
            "category": row[4],
            "seconds_watched": row[5],
            "watched_at": row[6]
            })
    return jsonify(videos)
        
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    init_db()
    app.run(port=5000)
    
