from flask import Flask, request, jsonify, redirect, make_response
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

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

    # --- LOGIC (UNCHANGED) ---
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
    # --- END LOGIC ---

    # --- NEW DESIGN (ENGLISH) ---
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Leaderboard | ESN Oslo Treasure Hunt</title>
        <style>
            :root {
                --primary: #0a2342;
                --primary-light: #1c3a63;
                --accent: #ffab00;
                --accent-glow: rgba(255, 171, 0, 0.3);
                --bg: #f4f6f9;
                --card-bg: #ffffff;
                --text-dark: #1a1a1a;
                --text-muted: #8898aa;
                --radius: 18px;
                --shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg); color: var(--text-dark); margin: 0; padding-bottom: 30px; -webkit-font-smoothing: antialiased;
            }
            .header {
                background: linear-gradient(135deg, var(--primary), var(--primary-light));
                color: white; padding: 15px 20px; position: sticky; top: 0; z-index: 100;
                box-shadow: 0 4px 15px rgba(10, 35, 66, 0.3);
                border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;
            }
            .header-content { max-width: 600px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { margin: 0; font-size: 1.1rem; font-weight: 800; letter-spacing: -0.5px; display: flex; flex-direction: column; line-height: 1.2;}
            .header h1 span.subtitle { font-size: 0.8rem; font-weight: 400; opacity: 0.8; }
            
            .nav-controls { display: flex; gap: 10px; align-items: center; }
            .btn-icon {
                background: rgba(255,255,255,0.15); border: none; color: white; width: 36px; height: 36px; border-radius: 50%;
                font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
            }
            .btn-icon:active { transform: scale(0.9); background: rgba(255,255,255,0.3); }
            .btn-nav {
                background: var(--accent); color: var(--primary); border: none; padding: 8px 16px; border-radius: 30px;
                font-weight: 700; font-size: 0.85rem; text-decoration: none; box-shadow: 0 4px 15px var(--accent-glow); transition: transform 0.2s;
                display: flex; align-items: center; gap: 6px;
            }
            .btn-nav:active { transform: translateY(2px); }
            
            .container { max-width: 600px; margin: 25px auto; padding: 0 15px; }
            
            .leaderboard-card {
                background: var(--card-bg); border-radius: var(--radius); overflow: hidden;
                box-shadow: var(--shadow); border: 1px solid rgba(0,0,0,0.03);
            }
            table { width: 100%; border-collapse: collapse; text-align: left; }
            th {
                background: #f8f9fa; color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;
                letter-spacing: 1px; padding: 15px; font-weight: 700; border-bottom: 2px solid #e9ecef;
            }
            td { padding: 15px; border-bottom: 1px solid #f0f0f0; vertical-align: middle; }
            tr:last-child td { border-bottom: none; }
            
            .rank-col { text-align: center; font-weight: 800; color: var(--primary-light); width: 50px; font-size: 1.1rem;}
            .team-col { font-weight: 600; font-size: 1.05rem; }
            .points-col { text-align: right; }
            .points-badge {
                background: var(--primary); color: var(--accent); padding: 6px 12px; border-radius: 20px;
                font-weight: 700; font-family: 'SF Mono', 'Roboto Mono', monospace; font-size: 1rem;
                box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
            }
            
            /* Special styles for Top 3 */
            .rank-1, .rank-2, .rank-3 { background-color: #ffffff; position: relative;}
            .rank-1 .rank-col { font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .rank-2 .rank-col { font-size: 2rem; }
            .rank-3 .rank-col { font-size: 1.6rem; }
            
            /* Subtle gradients for top 3 */
            .rank-1 { background: linear-gradient(to right, rgba(255, 215, 0, 0.05), rgba(255,255,255,0)); border-left: 4px solid #FFD700; }
            .rank-2 { background: linear-gradient(to right, rgba(192, 192, 192, 0.05), rgba(255,255,255,0)); border-left: 4px solid #C0C0C0; }
            .rank-3 { background: linear-gradient(to right, rgba(205, 127, 50, 0.05), rgba(255,255,255,0)); border-left: 4px solid #CD7F32; }
            
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>
                    ESN Oslo Hunt
                    <span class="subtitle">🏆 Leaderboard</span>
                </h1>
                <div class="nav-controls">
                    <button class="btn-icon" onclick="window.location.reload()" title="Refresh">🔄</button>
                    <a href="/events" class="btn-nav">📡 Live Feed</a>
                </div>
            </div>
        </div>

        <div class="container">
            <div class="leaderboard-card">
                <table>
                    <thead>
                        <tr><th class="rank-col">#</th><th>TEAM</th><th class="points-col">POINTS</th></tr>
                    </thead>
                    <tbody>
    """

    if not sorted_leaderboard:
         html += """<tr><td colspan="3" style="text-align:center; padding: 30px; color: #8898aa;">No scores recorded yet.</td></tr>"""

    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        rank_display = str(rank)
        row_class = ""
        
        if rank == 1:
            rank_display = "🥇"
            row_class = "rank-1"
        elif rank == 2:
            rank_display = "🥈"
            row_class = "rank-2"
        elif rank == 3:
            rank_display = "🥉"
            row_class = "rank-3"

        html += f"""
                        <tr class="{row_class}">
                            <td class="rank-col">{rank_display}</td>
                            <td class="team-col">{team.upper()}</td>
                            <td class="points-col"><span class="points-badge">{int(points)}</span></td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            // Auto-refresh every 30s
            console.log("Auto-refresh active: 30s");
            setTimeout(function(){ window.location.reload(1); }, 30000);
        </script>
    </body>
    </html>
    """
    return html

@app.route("/events", methods=["GET"])
def events_feed():
    all_events = []
    utc_tz = pytz.utc
    oslo_tz = pytz.timezone('Europe/Oslo')

    # --- LOGIC (UNCHANGED) ---
    for station_name in allowedStations:
        collection = db[station_name]
        entries = list(collection.find({}, {"team": 1, "timestamp": 1, "_id": 0}))
        for entry in entries:
            entry['station'] = station_name
            if 'timestamp' in entry:
                ts = entry['timestamp']
                if ts.tzinfo is None: ts = utc_tz.localize(ts)
                entry['timestamp_oslo'] = ts.astimezone(oslo_tz)
                all_events.append(entry)
    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)
    # --- END LOGIC ---

    # --- NEW DESIGN (ENGLISH) ---
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>Live Feed | ESN Oslo Treasure Hunt</title>
        <style>
            :root {
                --primary: #0a2342; /* Deep Night Blue */
                --primary-light: #1c3a63;
                --accent: #ffab00; /* Vibrant Gold */
                --accent-glow: rgba(255, 171, 0, 0.25);
                --bg: #f4f6f9;
                --card-bg: #ffffff;
                --text-dark: #1a1a1a;
                --text-muted: #6c757d;
                --radius: 16px;
                --shadow: 0 4px 20px rgba(0,0,0,0.08);
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: var(--bg); color: var(--text-dark); margin: 0; padding-bottom: 30px; -webkit-font-smoothing: antialiased;
            }
            .header {
                background: linear-gradient(135deg, var(--primary), var(--primary-light));
                color: white; padding: 15px 20px; position: sticky; top: 0; z-index: 100;
                box-shadow: 0 4px 15px rgba(10, 35, 66, 0.3);
                border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;
            }
            .header-content { max-width: 600px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }
            .header h1 { margin: 0; font-size: 1.1rem; font-weight: 800; letter-spacing: -0.5px; display: flex; flex-direction: column; line-height: 1.2;}
            .header h1 span.subtitle { font-size: 0.8rem; font-weight: 400; opacity: 0.8; }
            
            .nav-controls { display: flex; gap: 10px; align-items: center; }
            .btn-icon {
                background: rgba(255,255,255,0.15); border: none; color: white; width: 36px; height: 36px; border-radius: 50%;
                font-size: 1.2rem; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
            }
            .btn-icon:active { transform: scale(0.9); background: rgba(255,255,255,0.3); }
            .btn-nav {
                background: var(--accent); color: var(--primary); border: none; padding: 8px 16px; border-radius: 30px;
                font-weight: 700; font-size: 0.85rem; text-decoration: none; box-shadow: 0 4px 15px var(--accent-glow); transition: transform 0.2s;
                display: flex; align-items: center; gap: 6px;
            }
            .btn-nav:active { transform: translateY(2px); }
            
            .container { max-width: 600px; margin: 25px auto; padding: 0 15px; }
            
            .timeline-card {
                background: var(--card-bg); border-radius: var(--radius); padding: 18px; margin-bottom: 16px;
                box-shadow: var(--shadow); position: relative; overflow: hidden; border: 1px solid rgba(0,0,0,0.03);
            }
            /* Colored side indicator */
            .timeline-card::before {
                content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--primary);
            }
            .timeline-card.special::before { background: #ff0055; /* Different color for Teo/Alex */ }
            
            .card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
            .team-name { font-size: 1.15rem; font-weight: 800; color: var(--primary); margin: 0; }
            .timestamp { font-size: 0.8rem; color: var(--text-muted); display: flex; align-items: center; gap: 4px; background: #f0f2f5; padding: 4px 8px; border-radius: 10px; font-weight: 500;}
            
            .card-body { display: flex; align-items: center; gap: 10px; }
            .icon-marker { font-size: 1.4rem; }
            .station-badge {
                background: rgba(255, 171, 0, 0.1); color: #b37700; padding: 6px 12px; border-radius: 8px;
                font-family: 'SF Mono', 'Roboto Mono', monospace; font-weight: 700; letter-spacing: 0.5px; border: 1px solid rgba(255, 171, 0, 0.2);
            }
            .empty-state { text-align: center; color: var(--text-muted); margin-top: 60px; }
            .empty-icon { font-size: 4rem; margin-bottom: 20px; opacity: 0.5; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>
                    ESN Oslo Hunt
                    <span class="subtitle">📡 Live Feed</span>
                </h1>
                <div class="nav-controls">
                    <button class="btn-icon" onclick="window.location.reload()" title="Refresh">🔄</button>
                    <a href="/leaderboard" class="btn-nav">🏆 Leaderboard</a>
                </div>
            </div>
        </div>
        
        <div class="container">
    """

    if not all_events:
        html += """
            <div class="empty-state">
                <div class="empty-icon">💤</div>
                <h3>All quiet... for now!</h3>
                <p>Waiting for the first discoveries.</p>
            </div>"""
    
    for event in all_events:
        time_str = event['timestamp_oslo'].strftime("%H:%M")
        date_str = event['timestamp_oslo'].strftime("%d/%m")
        team_name = event.get('team', 'Unknown').upper()
        station_raw = event.get('station', 'Unknown')
        
        # Highlight logic for Teo/Alex
        special_class = "special" if station_raw in ["Teo", "Alex"] else ""

        html += f"""
            <div class="timeline-card {special_class}">
                <div class="card-header">
                    <h2 class="team-name">{team_name}</h2>
                    <span class="timestamp">🕒 {time_str} <small>({date_str})</small></span>
                </div>
                <div class="card-body">
                    <span class="icon-marker">📍</span>
                    <span>Unlocked: <span class="station-badge">{station_raw}</span></span>
                </div>
            </div>
        """

    html += """
        </div>
        <script>
            // Auto-refresh every 30s
            console.log("Auto-refresh active: 30s");
            setTimeout(function(){ window.location.reload(1); }, 30000);
        </script>
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