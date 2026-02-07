from flask import Flask, request, jsonify, redirect, render_template, session, url_for
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

# --- CONFIGURAZIONE ---
load_dotenv()

mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["TreasureHuntDB"]

# PASSWORD PER L'ADMIN
ADMIN_PASSWORD = "Racoon2k26"  # <--- CAMBIA QUESTA PASSWORD!
APP_SECRET_KEY = "CucurucucuPaloma" # Necessaria per i cookie

allowedStations = [
    "clue1-7K9P2L5N6Q3W", "clue2-R4T9YU2I6O1S", "clue3-F9G3HJ7K2LZ4",
    "clue4-X8CV6B1NM3Q9", "clue5-W5E1R3Y7U2I9", "clue6-O4P8AS1D7FG5",
    "clue7-H9JK3L1ZX7C2", "clue8-V9N4MQ2W8ER6", "clue9-T1YU5I9OP3S7",
    "clue10-D8G2HJ4K6LZ1", "clue11-X9CV5B3NM2Q8", "clue12-W7R4TY9U1IO3",
    "Teo", "Alex"
]
allowedTeams = [f"team{i}" for i in range(1, 101)]

app = Flask(__name__)
app.secret_key = APP_SECRET_KEY # Abilita le sessioni
CORS(app)

# --- HELPER FUNCTIONS ---

def get_oslo_time(timestamp):
    utc_tz = pytz.utc
    oslo_tz = pytz.timezone('Europe/Oslo')
    if timestamp.tzinfo is None:
        timestamp = utc_tz.localize(timestamp)
    return timestamp.astimezone(oslo_tz)

def is_game_active():
    config = db.config.find_one({"_id": "game_state"})
    if config:
        return config.get("active", False)
    db.config.insert_one({"_id": "game_state", "active": False})
    return False

def set_game_active(status: bool):
    db.config.update_one(
        {"_id": "game_state"},
        {"$set": {"active": status}},
        upsert=True
    )

# --- CONTEXT PROCESSOR ---
# Inietta variabili in tutti i template HTML automaticamente
@app.context_processor
def inject_globals():
    return dict(
        game_active=is_game_active(),
        is_admin=session.get('is_admin', False) # Dice al template se siamo loggati
    )

# --- ROTTE ADMIN / LOGIN ---

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password")
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True # Salva nella sessione
            return redirect('/events')
        else:
            error = "Wrong password!"
    return render_template('login.html', error=error)

@app.route("/logout")
def logout():
    session.pop('is_admin', None)
    return redirect('/events')

@app.route("/admin/toggle_game", methods=["POST"])
def toggle_game():
    # PROTEZIONE: Se non è admin, rimanda al login
    if not session.get('is_admin'):
        return redirect('/login')
        
    current_status = is_game_active()
    set_game_active(not current_status)
    return redirect(request.referrer or '/events')

# --- ROTTE STANDARD ---

@app.route("/", methods=["GET"])
def home():
    return redirect("https://scannerfuuun.vercel.app", code=302)

@app.route("/events", methods=["GET"])
def events_feed():
    all_events = []
    
    for station_name in allowedStations:
        collection = db[station_name]
        entries = list(collection.find({}, {"team": 1, "timestamp": 1, "_id": 0}))
        for entry in entries:
            entry['station'] = station_name
            if 'timestamp' in entry:
                entry['timestamp_oslo'] = get_oslo_time(entry['timestamp'])
                entry['ts_raw'] = entry['timestamp'].timestamp()
                all_events.append(entry)

    first_discoveries = {}
    for e in all_events:
        s = e['station']
        t = e['ts_raw']
        if s not in first_discoveries or t < first_discoveries[s]:
            first_discoveries[s] = t

    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)
    
    unique_teams = sorted(list(set(e.get('team', '') for e in all_events)))
    unique_stations = sorted(list(set(e.get('station', '') for e in all_events)))
    selected_team = request.args.get('team')
    selected_station = request.args.get('station')
    
    filtered_events = all_events
    if selected_team and selected_team != "all":
        filtered_events = [e for e in filtered_events if e.get('team') == selected_team]
    if selected_station and selected_station != "all":
        filtered_events = [e for e in filtered_events if e.get('station') == selected_station]

    display_events = []
    for event in filtered_events:
        is_first = (event['ts_raw'] == first_discoveries.get(event['station']))
        display_events.append({
            "team_display": event.get('team', 'Unknown').replace("team", "Team ").title(),
            "station": event.get('station', 'Unknown'),
            "time": event['timestamp_oslo'].strftime("%H:%M"),
            "is_special": event.get('station') in ["Teo", "Alex"],
            "is_first": is_first
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
        if station not in allowedStations: continue

        collection = db[station]
        entries = list(collection.find({}).sort("timestamp", 1))
        num_teams = len(entries)
        if num_teams == 0: continue
        
        bonus_points = round(120 / num_teams)
        for idx, entry in enumerate(entries):
            team = entry.get("team")
            if not team: continue
            if team not in leaderboard: leaderboard[team] = 0
            station_points = 20 + bonus_points
            if idx == 0: station_points *= 1.25
            leaderboard[team] += station_points

    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    
    display_board = []
    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        display_board.append({
            "rank": rank,
            "team": team.replace("team", "Team ").title(),
            "points": int(points)
        })

    return render_template('leaderboard.html', leaderboard=display_board)

@app.route("/<stationid>/<teamid>", methods=["GET"])
def handle_get_station_team(stationid, teamid):
    if not is_game_active():
        return jsonify({
            "status": "error",
            "message": "⛔ Game has not started yet (or is paused).",
            "game_active": False
        }), 200

    if stationid not in allowedStations:
        return jsonify({"error": "Invalid Station ID"}), 400
    if teamid not in allowedTeams:
        return jsonify({"error": "Invalid Team ID"}), 400

    station = stationid
    team = teamid
    collection = db[station]

    try:
        indexes = collection.index_information()
        if len(indexes) == 1:
            collection.create_index("team", unique=True)
    except Exception:
        pass

    try:
        collection.insert_one({
            "team": team,
            "timestamp": datetime.now()
        })
        return jsonify({
            "status": "success",
            "message": "✅ Check-in recorded!",
            "station": station,
            "team": team
        }), 200

    except Exception as e:
        return jsonify({
            "status": "warning",
            "message": "⚠️ Team already registered here.",
            "station": station,
            "team": team
        }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)