from flask import Flask, request,jsonify, render_template
from flask_cors import CORS # turns off restriction blocking webpage from talking to webpage
from dotenv import load_dotenv
import requests
import sqlite3
import os
import datetime

load_dotenv() #load .env for api key :>

app = Flask(__name__) 
CORS(app)
API_KEY = os.getenv("YOUTUBE_API_KEY")

DAILY_LIMIT_SECONDS = 30

SENT_EMAILS_DATES = set()

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
    c.execute("""
        CREATE TABLE IF NOT EXISTS email_log(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_date DATE
        )
    """)
    conn.commit()
    
    conn.close()
    
def check_today_limit():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
              SELECT SUM(seconds_watched)
              FROM videos
              WHERE Date(watched_at, 'localtime') = Date('now', 'localtime')
              """)
    row = c.fetchone()
    total_seconds = row[0] if row[0] is not None else 0
    print("total seconds watched today", total_seconds)
    
    limit_crossed = total_seconds >= DAILY_LIMIT_SECONDS
    print("limit exceeded?", limit_crossed)
    
    today_str = datetime.date.today().isoformat()
    c.execute("SELECT id FROM email_log WHERE sent_date =?", (today_str,))
    email_already_sent = c.fetchone() is not None
    
    should_send_email = False
    if limit_crossed and not email_already_sent:
        SENT_EMAILS_DATES.add(today_str)
        c.execute("INSERT INTO email_log (sent_date) VALUES (?)", (today_str,))
        conn.commit()
        should_send_email = True
    
    print("total seconds today:", total_seconds)
    print("limit crossed:", limit_crossed)
    print("email already sent:", email_already_sent)
    print("should send email:", should_send_email)
    conn.close()  
    return{"limitExceeded": limit_crossed, "shouldSendEmail": should_send_email}

@app.route("/track", methods=["POST"]) #runs when someone sends a req to /track, sends data
def track():
    data = request.json
    print("recieved data", data)
    video_id = data["video_id"]
    seconds_watched = data.get("secondsWatched", 0)
    print("recieved video with watch time", video_id, seconds_watched)
    
    if not video_id:
        return jsonify({"status": "ignored", "limitExceeded": False, "shouldSendEmail": False})
    
    existing = sqlite3.connect("videos.db")
    c = existing.cursor()
    c.execute("SELECT id, seconds_watched FROM videos WHERE video_id = ? ORDER BY watched_at DESC LIMIT 1", (video_id,))
    row = c.fetchone()
    
    if row and seconds_watched ==0:
        existing.close()
        limit_data = check_today_limit()
        return jsonify({"status": "duplicate", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})
    
    if row and seconds_watched > 0:
        c.execute("UPDATE videos SET seconds_watched = seconds_watched + ? WHERE id = ?", (seconds_watched, row[0]))
        existing.commit()
        existing.close()
        limit_data = check_today_limit()
        return jsonify({"status": "updated", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})
    existing.close()
       
    info = requests.get(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "id": video_id,
            "part": "snippet,contentDetails",
            "key": API_KEY
        }
    ).json()
    
    if not info.get("items"):
        return jsonify({"status": "error", "message": "vid not foudn", "limitExceeded": False, "shouldSendEmail": False})
    

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
    
    limit_data = check_today_limit()
    return jsonify({"status": "ok", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})

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

@app.route("/daily", methods=["GET"])
def get_daily():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("""
              SELECT DATE(watched_at, 'localtime') as day, SUM(seconds_watched) as total_seconds
              FROM videos
              GROUP BY DATE(watched_at, 'localtime')
              ORDER BY day DESC
    """)
    rows = c.fetchall()
    conn.close()
    
    daily = []
    for row in rows:
        daily.append({
            "date": row[0],
            "total_seconds": row[1]
        })
    return jsonify(daily)
              
@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.route("/clear", methods=["POST"])
def clear_db():
    conn = sqlite3.connect("videos.db")
    c = conn.cursor()
    c.execute("DELETE FROM videos")
    c.execute("DELETE FROM email_log")
    conn.commit()
    conn.close()
    return jsonify ({"status": "cleared"})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
    
