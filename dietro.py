from flask import Flask, request, jsonify, redirect, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

# Load environment variables
load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["TreasureHuntDB"]

# Configurazione
allowedStations = [
    "clue1-7K9P2L5N6Q3W", "clue2-R4T9YU2I6O1S", "clue3-F9G3HJ7K2LZ4",
    "clue4-X8CV6B1NM3Q9", "clue5-W5E1R3Y7U2I9", "clue6-O4P8AS1D7FG5",
    "clue7-H9JK3L1ZX7C2", "clue8-V9N4MQ2W8ER6", "clue9-T1YU5I9OP3S7",
    "clue10-D8G2HJ4K6LZ1", "clue11-X9CV5B3NM2Q8", "clue12-W7R4TY9U1IO3",
    "Teo", "Alex"
]
allowedTeams = [f"team{i}" for i in range(1,101)]

app = Flask(__name__)
CORS(app)

# Helper function per le date
def get_oslo_time(timestamp):
    utc_tz = pytz.utc
    oslo_tz = pytz.timezone('Europe/Oslo')
    if timestamp.tzinfo is None:
        timestamp = utc_tz.localize(timestamp)
    return timestamp.astimezone(oslo_tz)

@app.route("/", methods=["GET"])
def home():
    return redirect("https://scannerfuuun.vercel.app", code=302)

@app.route("/events", methods=["GET"])
def events_feed():
    all_events = []
    
    # Recupera dati
    for station_name in allowedStations:
        collection = db[station_name]
        entries = list(collection.find({}, {"team": 1, "timestamp": 1, "_id": 0}))
        for entry in entries:
            entry['station'] = station_name
            if 'timestamp' in entry:
                entry['timestamp_oslo'] = get_oslo_time(entry['timestamp'])
                all_events.append(entry)

    # Ordina
    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)
    
    # Filtri per la UI
    unique_teams = sorted(list(set(e.get('team', '') for e in all_events)))
    unique_stations = sorted(list(set(e.get('station', '') for e in all_events)))

    # Applica Filtri
    selected_team = request.args.get('team')
    selected_station = request.args.get('station')
    
    filtered_events = all_events
    if selected_team and selected_team != "all":
        filtered_events = [e for e in filtered_events if e.get('team') == selected_team]
    if selected_station and selected_station != "all":
        filtered_events = [e for e in filtered_events if e.get('station') == selected_station]

    # Formattazione dati per il template
    display_events = []
    for event in filtered_events:
        display_events.append({
            "team_raw": event.get('team', 'Unknown'),
            "team_display": event.get('team', 'Unknown').replace("team", "Team ").title(),
            "station": event.get('station', 'Unknown'),
            "time": event['timestamp_oslo'].strftime("%H:%M"),
            "is_special": event.get('station') in ["Teo", "Alex"]
        })

    return render_template(
        'events.html', 
        events=display_events, 
        teams=unique_teams, 
        stations=unique_stations,
        sel_team=selected_team, 
        sel_station=selected_station,
        count=len(filtered_events)
    )

@app.route("/leaderboard", methods=["GET"])
def leanderboard():
    leaderboard = {}
    stations = db.list_collection_names()

    for station in stations:
        collection = db[station]
        entries = list(collection.find({}).sort("timestamp", 1))
        num_teams = len(entries)
        if num_teams == 0: continue
        
        bonus_points = round(120 / num_teams)
        for idx, entry in enumerate(entries):
            team = entry["team"]
            if team not in leaderboard: leaderboard[team] = 0
            station_points = 20 + bonus_points
            if idx == 0: station_points *= 1.25
            leaderboard[team] += station_points

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    
    # Formatta per il template
    display_board = []
    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        display_board.append({
            "rank": rank,
            "team": team.replace("team", "Team ").title(),
            "points": int(points)
        })

    return render_template('leaderboard.html', leaderboard=display_board)

# ... (Lascia pure le altre rotte /post e /<stationid>/<teamid> come erano) ...
# ... (Inserisci qui il resto del tuo codice per il tracking) ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)