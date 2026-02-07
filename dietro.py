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
    
    # Timezone for display
    oslo_tz = pytz.timezone('Europe/Oslo')
    now_oslo = datetime.now(oslo_tz).strftime("%H:%M:%S")

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
    
    # Sort
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    # --- END LOGIC ---

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta http-equiv="refresh" content="30"> <title>Leaderboard | ESN Oslo Treasure Hunt</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #f0f4f8;
                --header-bg: #0f172a;
                --card-bg: #ffffff;
                --text-main: #1e293b;
                --text-muted: #94a3b8;
                --accent-color: #0ea5e9;
                --gold: #fbbf24;
                --silver: #e2e8f0;
                --bronze: #d97706;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding-bottom: 40px;
            }}

            /* Header */
            .header {{
                background-color: var(--header-bg);
                color: white;
                padding: 20px;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
            }}

            .header-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 600px;
                margin: 0 auto;
            }}

            h1 {{
                margin: 0;
                font-size: 1.25rem;
                font-weight: 800;
                line-height: 1.2;
            }}
            
            h1 span {{
                display: block;
                font-size: 0.85rem;
                font-weight: 500;
                opacity: 0.8;
                margin-top: 4px;
            }}

            .btn-group {{ display: flex; gap: 12px; }}

            .btn {{
                border: none;
                cursor: pointer;
                border-radius: 50px;
                padding: 10px 16px;
                font-size: 0.9rem;
                font-weight: 600;
                transition: transform 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
            }}

            .btn-refresh {{ background: rgba(255, 255, 255, 0.1); color: white; }}
            .btn-refresh:active {{ transform: scale(0.95); background: rgba(255,255,255,0.2); }}

            .btn-nav {{ background: var(--accent-color); color: white; box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3); }}
            .btn-nav:active {{ transform: translateY(2px); }}

             .status-bar {{
                text-align: center;
                font-size: 0.75rem;
                color: rgba(255,255,255,0.5);
                margin-top: 8px;
            }}

            /* List Container */
            .container {{
                max-width: 600px;
                margin: 24px auto;
                padding: 0 16px;
            }}

            .leaderboard-card {{
                background: var(--card-bg);
                border-radius: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
            }}

            th {{
                text-align: left;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                color: var(--text-muted);
                padding: 16px 20px;
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            td {{
                padding: 16px 20px;
                border-bottom: 1px solid #f1f5f9;
                vertical-align: middle;
            }}

            tr:last-child td {{ border-bottom: none; }}

            /* Columns */
            .rank-col {{ width: 50px; text-align: center; font-weight: 800; color: var(--text-muted); font-size: 1.1rem; }}
            .team-col {{ font-weight: 600; color: var(--text-main); font-size: 1.05rem; text-transform: capitalize; }}
            .points-col {{ text-align: right; }}

            .points-pill {{
                background-color: var(--header-bg);
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-weight: 700;
                font-size: 0.9rem;
                font-family: 'Inter', monospace;
            }}

            /* Top 3 Styling */
            .rank-1 {{ background: linear-gradient(to right, rgba(251, 191, 36, 0.1), transparent); }}
            .rank-1 .rank-col {{ font-size: 1.8rem; text-shadow: 0 2px 0 rgba(0,0,0,0.1); }}
            
            .rank-2 {{ background: linear-gradient(to right, rgba(226, 232, 240, 0.4), transparent); }}
            .rank-2 .rank-col {{ font-size: 1.5rem; }}

            .rank-3 {{ background: linear-gradient(to right, rgba(217, 119, 6, 0.1), transparent); }}
            .rank-3 .rank-col {{ font-size: 1.3rem; }}

        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-top">
                <h1>
                    ESN Oslo Hunt
                    <span>Leaderboard</span>
                </h1>
                <div class="btn-group">
                    <button class="btn btn-refresh" onclick="window.location.reload();">🔄</button>
                    <a href="/events" class="btn btn-nav">📡 Feed</a>
                </div>
            </div>
            <div class="status-bar">Last updated: {now_oslo}</div>
        </div>

        <div class="container">
            <div class="leaderboard-card">
                <table>
                    <thead>
                        <tr>
                            <th class="rank-col">#</th>
                            <th>Team</th>
                            <th class="points-col">Score</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    if not sorted_leaderboard:
         html += """<tr><td colspan="3" style="text-align:center; padding: 40px; color: #94a3b8;">No scores yet.</td></tr>"""

    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        rank_display = str(rank)
        row_class = ""
        
        # Formattazione nome team (es. "team1" -> "Team 1")
        team_display = team.replace("team", "Team ").title()

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
                            <td class="team-col">{team_display}</td>
                            <td class="points-col"><span class="points-pill">{int(points)}</span></td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
        </div>
        <script>
            setTimeout(() => {
                window.location.reload();
            }, 30000);
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
                if ts.tzinfo is None:
                    ts = utc_tz.localize(ts)
                entry['timestamp_oslo'] = ts.astimezone(oslo_tz)
                all_events.append(entry)

    # Sort logic
    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)
    
    # Get current time for "Last updated"
    now_oslo = datetime.now(oslo_tz).strftime("%H:%M:%S")

    # --- NEW DESIGN & FIXES ---
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <meta http-equiv="refresh" content="30"> <title>Live Feed | ESN Oslo Treasure Hunt</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #f0f4f8;
                --header-bg: #0f172a; /* Nordic Night */
                --card-bg: #ffffff;
                --text-main: #1e293b;
                --text-secondary: #64748b;
                --accent-color: #0ea5e9; /* Sky Blue */
                --special-accent: #f59e0b; /* Amber/Gold */
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                margin: 0;
                padding-bottom: 40px;
                -webkit-font-smoothing: antialiased;
            }}

            /* Header Design */
            .header {{
                background-color: var(--header-bg);
                color: white;
                padding: 20px;
                position: sticky;
                top: 0;
                z-index: 1000;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
            }}

            .header-top {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                max-width: 600px;
                margin: 0 auto;
            }}

            h1 {{
                margin: 0;
                font-size: 1.25rem;
                font-weight: 800;
                letter-spacing: -0.02em;
                line-height: 1.2;
            }}
            
            h1 span {{
                display: block;
                font-size: 0.85rem;
                font-weight: 500;
                opacity: 0.8;
                margin-top: 4px;
            }}

            /* Buttons */
            .btn-group {{
                display: flex;
                gap: 12px;
            }}

            .btn {{
                border: none;
                cursor: pointer;
                border-radius: 50px;
                padding: 10px 16px;
                font-size: 0.9rem;
                font-weight: 600;
                transition: all 0.2s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}

            .btn-refresh {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                backdrop-filter: blur(5px);
            }}

            .btn-refresh:active {{
                transform: scale(0.95);
                background: rgba(255, 255, 255, 0.2);
            }}

            .btn-nav {{
                background: var(--accent-color);
                color: white;
                box-shadow: 0 4px 12px rgba(14, 165, 233, 0.3);
            }}

            .btn-nav:active {{
                transform: translateY(2px);
            }}

            /* Last Updated Indicator */
            .status-bar {{
                text-align: center;
                font-size: 0.75rem;
                color: rgba(255,255,255,0.5);
                margin-top: 8px;
            }}

            /* Feed Container */
            .container {{
                max-width: 600px;
                margin: 24px auto;
                padding: 0 16px;
            }}

            /* Timeline Cards */
            .feed-card {{
                background: var(--card-bg);
                border-radius: 16px;
                padding: 20px;
                margin-bottom: 16px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.03);
                border: 1px solid rgba(255,255,255,0.5);
                display: flex;
                flex-direction: column;
                gap: 12px;
                position: relative;
                overflow: hidden;
            }}

            .feed-card::before {{
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 6px;
                background-color: var(--accent-color);
            }}

            /* Special styling for Teo/Alex */
            .feed-card.special::before {{
                background-color: var(--special-accent);
            }}

            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .team-name {{
                font-size: 1.1rem;
                font-weight: 700;
                color: var(--text-main);
                text-transform: capitalize; /* Elegant capitalization */
            }}

            .timestamp {{
                font-size: 0.8rem;
                color: var(--text-secondary);
                background: #f1f5f9;
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: 500;
            }}

            .card-body {{
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.95rem;
                color: var(--text-secondary);
            }}

            .station-badge {{
                background-color: #e0f2fe;
                color: #0369a1;
                padding: 6px 12px;
                border-radius: 8px;
                font-family: 'Inter', monospace;
                font-weight: 600;
                font-size: 0.9rem;
            }}
            
            .feed-card.special .station-badge {{
                background-color: #fef3c7;
                color: #b45309;
            }}

            .empty-state {{
                text-align: center;
                padding: 40px;
                color: var(--text-secondary);
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-top">
                <h1>
                    ESN Oslo Hunt
                    <span>Live Feed</span>
                </h1>
                <div class="btn-group">
                    <button class="btn btn-refresh" onclick="window.location.reload();">
                        🔄
                    </button>
                    <a href="/leaderboard" class="btn btn-nav">
                        🏆 Rank
                    </a>
                </div>
            </div>
            <div class="status-bar">Last updated: {now_oslo}</div>
        </div>
        
        <div class="container">
    """

    if not all_events:
        html += """
            <div class="empty-state">
                <div style="font-size: 3rem; margin-bottom: 10px;">💤</div>
                <h3>No activity yet</h3>
                <p>The hunt hasn't started or no clues found yet.</p>
            </div>"""
    
    for event in all_events:
        time_str = event['timestamp_oslo'].strftime("%H:%M")

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