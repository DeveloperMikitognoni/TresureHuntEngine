from flask import Flask, request, jsonify, redirect, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz

# --- 1. CONFIGURAZIONE ---

# Carica variabili d'ambiente dal file .env
load_dotenv()

# Connessione a MongoDB
mongo_uri = os.getenv("MONGO_URI")
client = MongoClient(mongo_uri)
db = client["TreasureHuntDB"]

# Liste di controllo (Whitelist)
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
]

# Genera team1 ... team100
allowedTeams = [f"team{i}" for i in range(1, 101)]

app = Flask(__name__)
# Abilita CORS per permettere chiamate da domini diversi (es. scanner)
CORS(app)


# --- 2. HELPER FUNCTIONS ---

def get_oslo_time(timestamp):
    """Converte un timestamp (UTC o naive) nel fuso orario di Oslo."""
    utc_tz = pytz.utc
    oslo_tz = pytz.timezone('Europe/Oslo')
    
    # Se il timestamp non ha info sul fuso, assumiamo sia UTC
    if timestamp.tzinfo is None:
        timestamp = utc_tz.localize(timestamp)
        
    return timestamp.astimezone(oslo_tz)


# --- 3. ROTTE WEB (UI) ---

@app.route("/", methods=["GET"])
def home():
    """Reindirizza alla pagina dello scanner."""
    return redirect("https://scannerfuuun.vercel.app", code=302)


@app.route("/events", methods=["GET"])
def events_feed():
    """Pagina Live Feed con filtri e nuova grafica."""
    all_events = []
    
    # Raccogli dati da tutte le stazioni
    for station_name in allowedStations:
        collection = db[station_name]
        # Prendi team e timestamp, escludi _id di Mongo
        entries = list(collection.find({}, {"team": 1, "timestamp": 1, "_id": 0}))
        
        for entry in entries:
            entry['station'] = station_name
            if 'timestamp' in entry:
                # Converti orario per visualizzazione corretta
                entry['timestamp_oslo'] = get_oslo_time(entry['timestamp'])
                all_events.append(entry)

    # Ordina dal più recente al più vecchio
    all_events.sort(key=lambda x: x['timestamp_oslo'], reverse=True)
    
    # --- Gestione Filtri ---
    # Trova team e stazioni unici per popolare i menu a tendina
    unique_teams = sorted(list(set(e.get('team', '') for e in all_events)))
    unique_stations = sorted(list(set(e.get('station', '') for e in all_events)))

    # Leggi filtri dall'URL (es: ?team=team1)
    selected_team = request.args.get('team')
    selected_station = request.args.get('station')
    
    filtered_events = all_events

    if selected_team and selected_team != "all":
        filtered_events = [e for e in filtered_events if e.get('team') == selected_team]
    
    if selected_station and selected_station != "all":
        filtered_events = [e for e in filtered_events if e.get('station') == selected_station]

    # Prepara i dati per il template HTML (formattazione stringhe)
    display_events = []
    for event in filtered_events:
        display_events.append({
            "team_raw": event.get('team', 'Unknown'),
            # "team1" diventa "Team 1"
            "team_display": event.get('team', 'Unknown').replace("team", "Team ").title(),
            "station": event.get('station', 'Unknown'),
            # Orario formattato HH:MM
            "time": event['timestamp_oslo'].strftime("%H:%M"),
            # Flag per grafica speciale
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
    """Pagina Classifica con calcolo punteggi."""
    leaderboard = {}
    stations = db.list_collection_names()

    for station in stations:
        # Salta collezioni non pertinenti se ce ne sono
        if station not in allowedStations:
            continue

        collection = db[station]
        entries = list(collection.find({}).sort("timestamp", 1))
        num_teams = len(entries)
        
        if num_teams == 0:
            continue
        
        # Logica punteggio dinamico
        bonus_points = round(120 / num_teams)
        
        for idx, entry in enumerate(entries):
            team = entry["team"]
            if team not in leaderboard:
                leaderboard[team] = 0
            
            station_points = 20 + bonus_points
            
            # Bonus primo arrivato (+25%)
            if idx == 0:
                station_points *= 1.25
            
            leaderboard[team] += station_points

    # Ordina decrescente per punti
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    
    # Prepara dati per template
    display_board = []
    for rank, (team, points) in enumerate(sorted_leaderboard, start=1):
        display_board.append({
            "rank": rank,
            "team": team.replace("team", "Team ").title(),
            "points": int(points)
        })

    return render_template('leaderboard.html', leaderboard=display_board)


# --- 4. API CHECK-IN (CORE LOGIC) ---

@app.route("/<stationid>/<teamid>", methods=["GET"])
def handle_get_station_team(stationid, teamid):
    """
    Gestisce la scansione del QR Code.
    Esempio URL: /clue1-XXXX/team5
    """
    
    # Validazione Input
    if stationid not in allowedStations:
        return jsonify({"error": "Invalid Station ID"}), 400
    
    if teamid not in allowedTeams:
        return jsonify({"error": "Invalid Team ID"}), 400

    station = stationid
    team = teamid
    collection = db[station]

    # Assicura che un team non possa registrarsi due volte nella stessa stazione
    # Crea un indice unico sul campo 'team' se non esiste
    try:
        indexes = collection.index_information()
        # Se c'è solo l'indice _id_, crea quello nuovo
        if len(indexes) == 1:
            collection.create_index("team", unique=True)
    except Exception:
        pass

    # Tenta l'inserimento
    try:
        collection.insert_one({
            "team": team,
            "timestamp": datetime.now()  # Salva in UTC
        })
        
        # Risposta di Successo
        return jsonify({
            "status": "success",
            "message": "Check-in recorded successfully!",
            "station": station,
            "team": team
        }), 200

    except Exception as e:
        # Se fallisce (es. DuplicateKeyError), il team è già stato qui
        return jsonify({
            "status": "warning",
            "message": "Team already registered at this station.",
            "station": station,
            "team": team,
            "error_details": str(e)
        }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "404 Not Found"}), 404


if __name__ == "__main__":
    # Avvia il server sulla porta 80
    app.run(host="0.0.0.0", port=80, debug=False)