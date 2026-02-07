from flask import Flask, request, jsonify, redirect, make_response
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from the environment variables
mongo_uri = os.getenv("MONGO_URI")
# Connect to MongoDB (update the URI with your MongoDB URL)
client = MongoClient(mongo_uri)
db = client["TreasureHuntDB"]  # Database namet

# secretToStation = {
#     "apple-mango-QF":"station1",
#     "banana-pear-ZX": "station2",
#     "cherry-lemon-KJ":"station3",
#     "grape-peach-MN":"station4",
#     "melon-apple-RT":"station5",
#     "peach-banana-LD":"station6",
#    "orange-mango-WQ":"station7",
#     "lemon-cherry-PV":"station8",
#     "mango-pear-KT":"station9",
#     "apple-grape-HS":"station10",
#     "coral-bike-LS":"station11",
#     "mine-river-TP":"station12",
# }

# Create a list of strings

allowedStations = [
    "clue1-7K9P2L5N6Q3W",
    "clue2-R4T9YU2I6O1S",
    "clue3-F9G3HJ7K2LZ4",
    "clue4-X8CV6B1NM3Q9",
    "clue5-W5E1R3Y7U2I9",
    "clue6-O4P8AS1D7FG5",
    "clue7-H9JK3L1ZX7C2",
    "clue8-V9N4MQ2W8ER6",
    "clue9-T1YU5I9OP3S7",
    "clue10-D8G2HJ4K6LZ1",
    "clue11-X9CV5B3NM2Q8",
    "clue12-W7R4TY9U1IO3",
    "Teo",
    "Alex"
];
allowedTeams = [f"team{i}" for i in range(1,101)]
#allowedStations = []
#allowedTeams = []


app = Flask(__name__)
CORS(app)

@app.after_request
def add_csp_header(response):
    response.headers["Content-Security-Policy"] = "default-src 'self';"
    return response

# Define a route for GET requests
@app.route("/", methods=["GET"])
def home():
    #return jsonify({"message": "Welcome to the Flask API!"})
    # Redirect to scanner
    return redirect("https://scannerfuuun.vercel.app", code=302)  # 302 = temporary redirect


@app.route("/leaderboard", methods=["GET"])
def leanderboard():
    leaderboard = {}
    stations = db.list_collection_names()

    # --- LOGICA CALCOLO PUNTI (INVARIATA) ---
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

    # --- HTML ---
    html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Classifica</title>
        <style>
            :root {
                --primary: #0056b3;
                --accent: #ff9800;
                --bg: #f0f2f5;
                --card-bg: #ffffff;
                --text: #333;
            }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); margin: 0; color: var(--text); }
            
            .header {
                background-color: var(--primary);
                color: white;
                padding: 15px;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .header h1 { margin: 0 0 10px 0; font-size: 1.4rem; }
            
            .nav-row {
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            .btn {
                padding: 6px 14px;
                border-radius: 20px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.9rem;
                border: none;
                cursor: pointer;
                transition: transform 0.1s;
            }
            .btn:active { transform: scale(0.95); }
            
            .btn-refresh { background: rgba(255,255,255,0.2); color: white; }
            .btn-link { background: var(--accent); color: white; }

            .container { max-width: 600px; margin: 20px auto; padding: 0 15px; }
            .card { background: var(--card-bg); border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); overflow: hidden; }
            table { width: 100%; border-collapse: collapse; text-align: left; }
            th { background: #e9ecef; color: #666; font-size: 0.85rem; padding: 12px 15px; }
            td { padding: 15px; border-bottom: 1px solid #f0f0f0; }
            .rank-col { text-align: center; font-weight: bold; color: var(--primary); width: 50px; }
            .points-col { text-align: right; font-weight: bold; color: var(--accent); font-family: monospace; font-size: 1.1rem; }
            
            /* Primi 3 posti */
            tr:nth-child(1) .rank-col { font-size: 1.5rem; }
            tr:nth-child(2) .rank-col { font-size: 1.3rem; }
            tr:nth-child(3) .rank-col { font-size: 1.1rem; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏆 Classifica</h1>
            <div class="nav-row">
                <button class="btn btn-refresh" onclick="window.location.reload()">🔄 Aggiorna</button>
                <a href="/events" class="btn btn-link">📡 Vedi Feed</a>
            </div>
        </div>

        <div class="container">
            <div class="card">
                <table>
                    <thead>
                        <tr><th class="rank-col">#</th><th>Team</th><th class="points-col">Pt</th></tr>
                    </thead>
                    <tbody>
    """

    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        rank_display = str(rank)
        if rank == 1: rank_display = "🥇"
        elif rank == 2: rank_display = "🥈"
        elif rank == 3: rank_display = "🥉"

        html += f"""
                        <tr>
                            <td class="rank-col">{rank_display}</td>
                            <td>{team}</td>
                            <td class="points-col">{int(points)}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <script>setTimeout(function(){ window.location.reload(1); }, 30000);</script>
    </body>
    </html>
    """
    return html

@app.route("/events", methods=["GET"])
def events_feed():
    all_events = []
    
    # Definisci i fusi orari
    utc_tz = pytz.utc
    oslo_tz = pytz.timezone('Europe/Oslo')

    # 1. Recupera i dati
    for station_name in allowedStations:
        collection = db[station_name]
        entries = list(collection.find({}, {"team": 1, "timestamp": 1, "_id": 0}))
        
        for entry in entries:
            entry['station'] = station_name
            if 'timestamp' in entry:
                ts = entry['timestamp']
                if ts.tzinfo is None:
                    ts = utc_tz.localize(ts)
                entry['timestamp_oslo'] = ts.astimezone(oslo_tz)
                all_events.append(entry)

    # 2. Ordina
    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)

    # 3. HTML
    html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Live Feed</title>
        <style>
            :root {
                --primary: #0056b3;
                --accent: #ff9800;
                --bg: #f0f2f5;
                --card-bg: #ffffff;
                --text: #333;
                --subtext: #666;
            }
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); margin: 0; color: var(--text); }
            
            .header {
                background-color: var(--primary);
                color: white;
                padding: 15px;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .header h1 { margin: 0 0 10px 0; font-size: 1.2rem; }
            
            .nav-row {
                display: flex;
                justify-content: center;
                gap: 10px;
            }
            .btn {
                padding: 6px 14px;
                border-radius: 20px;
                text-decoration: none;
                font-weight: 600;
                font-size: 0.9rem;
                border: none;
                cursor: pointer;
                transition: transform 0.1s;
            }
            .btn:active { transform: scale(0.95); }
            
            .btn-refresh { background: rgba(255,255,255,0.2); color: white; }
            .btn-link { background: var(--accent); color: white; }

            .container { max-width: 600px; margin: 0 auto; padding: 20px 15px; }
            .timeline-item {
                background: var(--card-bg);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                border-left: 5px solid var(--primary);
            }
            .meta-row { display: flex; justify-content: space-between; margin-bottom: 8px; }
            .time { font-size: 0.85rem; color: var(--subtext); background: #eee; padding: 4px 8px; border-radius: 6px; }
            .team { font-weight: bold; color: var(--primary); }
            .station-code { font-family: monospace; background: #fff3cd; padding: 2px 6px; border-radius: 4px; color: #856404; }
            .empty-state { text-align: center; color: var(--subtext); margin-top: 50px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📡 Live Feed</h1>
            <div class="nav-row">
                <button class="btn btn-refresh" onclick="window.location.reload()">🔄 Aggiorna</button>
                <a href="/leaderboard" class="btn btn-link">🏆 Classifica</a>
            </div>
        </div>
        
        <div class="container">
    """

    if not all_events:
        html += """<div class="empty-state"><h3>Nessun evento!</h3></div>"""
    
    for event in all_events:
        time_str = event['timestamp_oslo'].strftime("%H:%M:%S")
        date_str = event['timestamp_oslo'].strftime("%d %b")
        team_name = event.get('team', 'Unknown')
        station_raw = event.get('station', 'Unknown')
        border_color = "var(--accent)" if station_raw in ["Teo", "Alex"] else "var(--primary)"

        html += f"""
            <div class="timeline-item" style="border-left-color: {border_color};">
                <div class="meta-row">
                    <span class="team">{team_name}</span>
                    <span class="time">{time_str} <small>({date_str})</small></span>
                </div>
                <div>📍 Ha trovato: <span class="station-code">{station_raw}</span></div>
            </div>
        """

    html += """
        </div>
        <script>setTimeout(function(){ window.location.reload(1); }, 30000);</script>
    </body>
    </html>
    """
    return html

# Define a route for POST requests
@app.route("/post", methods=["POST"])
def handle_post():
    # data = request.get_json()
    # if not data:
    #     return jsonify({"error": "No JSON data provided"}), 400

    # # Validate the expected keys
    # if "station" not in data or "team" not in data:
    #     return jsonify({"error": "Invalid JSON payload. 'station' and 'team' are required."}), 400

    # # Process the data
    # station = data["station"]
    # team = data["team"]

    return jsonify({
        "message": "You won all the code is on github (TresureHuntEngine) hack it to win to Lapponia voyage!",
    }), 200

# Define a route for GET requests with dynamic stationid and teamid
@app.route("/<stationid>/<teamid>", methods=["GET"])
def handle_get_station_team(stationid, teamid):
    # Save the stationid and teamid in Python variables (already strings)
    if stationid in allowedStations and teamid in allowedTeams:
        station = stationid
        team = teamid
    else:
        return jsonify({"error": "Invalid station or team ID"}), 400
    # Get or create the collection for the station
    collection = db[station]
    print(collection.index_information())
    if (len(collection.index_information())==1):
        collection.create_index("team", unique=True)

    # Insert the team ID and timestamp into the collection
    try:
        collection.insert_one({
            "team": team,
            "timestamp": datetime.now()
        })
    except Exception as e:
        return jsonify({
        "message": "Error: Possibly duplicate team entry.",
        "station": station,
        "team": team,
        "errorMessage": str(e)
    }), 200

    # Return the extracted values
    return jsonify({
        "message": "GET request received!",
        "station": station,
        "team": team
    }), 200

# Define a route for handling 404 errors
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)