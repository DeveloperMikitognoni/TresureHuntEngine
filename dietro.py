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
allowedTeams = [f"team{i}" for i in range(1,100)]
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

    for station in stations:
        collection = db[station]
        entries = list(collection.find({}).sort("timestamp", 1))
        num_teams = len(entries)
        if num_teams == 0:
            continue
        
        bonus_points = round(120 / num_teams)
        
        for idx, entry in enumerate(entries):
            team = entry["team"]
            if team not in leaderboard:
                leaderboard[team] = 0
            
            # punti per questa stazione
            station_points = 20 + bonus_points
            
            # se è il primo → +25%
            if idx == 0:
                station_points *= 1.25
            
            leaderboard[team] += station_points
    # Sort the leaderboard by points in descending order
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)

    # Generate HTML content for the leaderboard
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Leaderboard</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f9;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            table {
                border-collapse: collapse;
                width: 80%;
                max-width: 600px;
                margin: 20px auto;
                background: #fff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }
            th, td {
                padding: 15px;
                text-align: left;
            }
            th {
                background-color: #007BFF;
                color: white;
                text-transform: uppercase;
            }
            tr:nth-child(even) {
                background-color: #f2f2f2;
            }
            tr:hover {
                background-color: #ddd;
            }
            h1 {
                text-align: center;
                color: #333;
            }
        </style>
    </head>
    <body>
        <div>
            <h1>Leaderboard</h1>
            <table>
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Team</th>
                        <th>Points</th>
                    </tr>
                </thead>
                <tbody>
    """

    # Add rows to the leaderboard table
    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        html += f"""
                    <tr>
                        <td>{rank}</td>
                        <td>{team}</td>
                        <td>{points}</td>
                    </tr>
        """

    # Close the HTML content
    html += """
                </tbody>
            </table>
        </div>
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