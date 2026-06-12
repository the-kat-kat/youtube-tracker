from flask import Flask, request,jsonify, render_template
from flask_cors import CORS 
from dotenv import load_dotenv
import requests
import psycopg
from psycopg_pool import ConnectionPool
import os
import datetime

load_dotenv() 
    
API_KEY = os.getenv("YOUTUBE_API_KEY")
DB_URL = os.getenv("DB_URL")

DAILY_LIMIT_SECONDS = 30 * 4

pool = ConnectionPool(DB_URL, min_size=1, max_size=5, open=True)
app = Flask(__name__) 
CORS(app)


def init_db():
    conn = pool.getconn()
    try:
        c = conn.cursor() 
        c.execute(""" 
            CREATE TABLE IF NOT EXISTS videos(
            id SERIAL PRIMARY KEY, 
            video_id TEXT,
            title TEXT,
            channel TEXT,
            duration TEXT,
            category TEXT,
            seconds_watched INTEGER DEFAULT 0,
            user_id TEXT DEFAULT 'default id',
            watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
            """) #triple quotes for mult line string
        c.execute("""
            CREATE TABLE IF NOT EXISTS email_log(
                id SERIAL PRIMARY KEY,
                sent_date DATE,
                user_id TEXT DEFAULT 'default_id'
            )
        """)
        conn.commit()
    finally:
        pool.putconn(conn)
    
def check_today_limit(user_id, conn):
    c = conn.cursor()
    c.execute("""
            SELECT SUM(seconds_watched)
            FROM videos
            WHERE Date(watched_at) = CURRENt_DATE
            AND user_id = %s
            """, (user_id,))
    row = c.fetchone()
    total_seconds = row[0] if row[0] is not None else 0
    print("total seconds watched today", total_seconds)
    
    limit_crossed = total_seconds >= DAILY_LIMIT_SECONDS
    print("limit exceeded?", limit_crossed)
    
    today_str = datetime.date.today()
    c.execute("SELECT id FROM email_log WHERE sent_date = %s AND  user_id = %s", (today_str, user_id,))
    email_already_sent = c.fetchone() is not None
    
    should_send_email = False
    if limit_crossed and not email_already_sent:
        c.execute("INSERT INTO email_log (sent_date, user_id) VALUES (%s, %s)", (today_str, user_id,))
        conn.commit()
        should_send_email = True
    
    print("total seconds today:", total_seconds)
    print("limit crossed:", limit_crossed)
    print("email already sent:", email_already_sent)
    print("should send email:", should_send_email)
    return{"limitExceeded": limit_crossed, "shouldSendEmail": should_send_email}

@app.route("/track", methods=["POST"])
def track():
    data = request.json
    print("recieved data", data)
    video_id = data.get("video_id")
    seconds_watched = data.get("secondsWatched", 0)
    user_id = data.get("user_id", "default id")
    print("recieved video with watch time", video_id, seconds_watched)
    
    if not video_id:
        return jsonify({"status": "ignored", "limitExceeded": False, "shouldSendEmail": False})
    
    conn = pool.getconn()
    try:
        c = conn.cursor()
        c.execute("SELECT id, seconds_watched FROM videos WHERE video_id = %s AND user_id = %s AND DATE(watched_at) = CURRENT_DATE ORDER BY watched_at DESC LIMIT 1", (video_id, user_id))
        row = c.fetchone()
        
        if row and seconds_watched ==0:
            limit_data = check_today_limit(user_id, conn)
            return jsonify({"status": "duplicate", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})
        
        if row and seconds_watched > 0:
            c.execute("UPDATE videos SET seconds_watched = seconds_watched + %s WHERE id = %s", (seconds_watched, row[0]))
            conn.commit()
            limit_data = check_today_limit(user_id, conn)
            return jsonify({"status": "updated", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})
        
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

        c.execute("INSERT INTO videos (video_id, title, channel, duration, category, user_id, seconds_watched) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (video_id, title, channel, duration, category, user_id, seconds_watched))
        conn.commit()
        
        limit_data = check_today_limit(user_id, conn)
        return jsonify({"status": "ok", "limitExceeded": limit_data["limitExceeded"], "shouldSendEmail": limit_data["shouldSendEmail"]})
    
    finally:
        pool.putconn(conn)
        
@app.route("/videos", methods=["GET"]) 
def get_videos():
    conn = pool.getconn()
    try:
        c = conn.cursor()
        c.execute("SELECT video_id, title, channel, duration, category, seconds_watched, watched_at FROM videos ORDER BY watched_at DESC") 
        rows = c.fetchall()
    finally:
        pool.putconn(conn)

    videos = []
    for row in rows:
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
    conn = pool.getconn()
    try:
        c = conn.cursor()
        c.execute("""
                SELECT DATE(watched_at) as day, SUM(seconds_watched) as total_seconds
                FROM videos
                GROUP BY DATE(watched_at)
                ORDER BY day DESC
        """)
        rows = c.fetchall()
    finally:
        pool.putconn(conn)
    
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
    conn = pool.getconn()
    try:
        c = conn.cursor()
        c.execute("TRUNCATE TABLE IF EXISTS videos, email_log RESTART IDENTITY")
        conn.commit()
    finally:
        pool.putconn(conn)
    return jsonify ({"status": "cleared"})

with app.app_context():
    init_db()

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
    
