from flask import Flask, request, jsonify, session
from flask_cors import CORS
import json
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = '501314'  # Změň na něco bezpečného
CORS(app)

# ============ DATA V PAMĚTI ============
# Struktura: {steam_id: {lat, lng, username, avatar, timestamp}}
players_positions = {}

# Struktura: {user_steam_id: [friend_steam_ids...]}
friend_lists = {}

# ============ STEAM AUTENTIFIKACE ============
# Pokud máš Steam login integrovaný, SessionID se nastaví tady

def get_steam_id_from_session():
    """Vrátí Steam ID z session"""
    return session.get('steam_id')

def require_steam_login(f):
    """Decorator pro kontrolu Steam loginu"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        steam_id = get_steam_id_from_session()
        if not steam_id:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============ POZICE HRÁČE ============

@app.route('/api/position', methods=['GET'])
@require_steam_login
def get_position():
    """Vrátí pozici aktuálního hráče"""
    steam_id = get_steam_id_from_session()
    
    if steam_id in players_positions:
        pos = players_positions[steam_id]
        return jsonify({
            'steam_id': steam_id,
            'lat': pos['lat'],
            'lng': pos['lng'],
            'username': pos.get('username'),
            'avatar': pos.get('avatar'),
            'timestamp': pos.get('timestamp')
        })
    
    # Výchozí pozice
    return jsonify({
        'steam_id': steam_id,
        'lat': 961.5,
        'lng': 960,
        'username': 'Unknown',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/position', methods=['POST'])
@require_steam_login
def update_position():
    """Aktualizuje pozici hráče"""
    steam_id = get_steam_id_from_session()
    data = request.get_json()
    
    if not data or 'lat' not in data or 'lng' not in data:
        return jsonify({'error': 'Missing lat/lng'}), 400
    
    players_positions[steam_id] = {
        'lat': float(data['lat']),
        'lng': float(data['lng']),
        'username': data.get('username', 'Unknown'),
        'avatar': data.get('avatar'),
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({'success': True, 'steam_id': steam_id})

# ============ PŘÁTELÉ ============

@app.route('/api/friends', methods=['GET'])
@require_steam_login
def get_friends():
    """Vrátí pozice přátel aktuálního hráče"""
    steam_id = get_steam_id_from_session()
    friends_ids = friend_lists.get(steam_id, [])
    
    friends = []
    for friend_id in friends_ids:
        if friend_id in players_positions:
            pos = players_positions[friend_id]
            friends.append({
                'steam_id': friend_id,
                'lat': pos['lat'],
                'lng': pos['lng'],
                'username': pos.get('username'),
                'avatar': pos.get('avatar'),
                'timestamp': pos.get('timestamp')
            })
    
    return jsonify({'friends': friends})

@app.route('/api/friends/add', methods=['POST'])
@require_steam_login
def add_friend():
    """Přidá přítele"""
    steam_id = get_steam_id_from_session()
    data = request.get_json()
    friend_id = data.get('friend_steam_id')
    
    if not friend_id:
        return jsonify({'error': 'Missing friend_steam_id'}), 400
    
    if steam_id not in friend_lists:
        friend_lists[steam_id] = []
    
    if friend_id not in friend_lists[steam_id]:
        friend_lists[steam_id].append(friend_id)
    
    return jsonify({'success': True})

@app.route('/api/friends/remove', methods=['POST'])
@require_steam_login
def remove_friend():
    """Odebere přítele"""
    steam_id = get_steam_id_from_session()
    data = request.get_json()
    friend_id = data.get('friend_steam_id')
    
    if steam_id in friend_lists and friend_id in friend_lists[steam_id]:
        friend_lists[steam_id].remove(friend_id)
    
    return jsonify({'success': True})

# ============ MARKERY ============

markers = {}

@app.route('/api/markers', methods=['POST'])
@require_steam_login
def add_marker():
    """Přidá marker na mapu"""
    steam_id = get_steam_id_from_session()
    data = request.get_json()
    
    if not data or 'name' not in data or 'lat' not in data or 'lng' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    marker_id = f"{steam_id}_{data.get('id', int(datetime.now().timestamp() * 1000))}"
    
    markers[marker_id] = {
        'steam_id': steam_id,
        'name': data['name'],
        'type': data.get('type', 'default'),
        'color': data.get('color', '#2196F3'),
        'lat': float(data['lat']),
        'lng': float(data['lng']),
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify({'success': True, 'marker_id': marker_id})

@app.route('/api/markers', methods=['GET'])
@require_steam_login
def get_markers():
    """Vrátí markery aktuálního hráče"""
    steam_id = get_steam_id_from_session()
    user_markers = [m for m in markers.values() if m['steam_id'] == steam_id]
    return jsonify({'markers': user_markers})

# ============ DEBUG ENDPOINTS ============

@app.route('/api/debug/login', methods=['POST'])
def debug_login():
    """DEBUG: Simulovaný login (smaž v produkci!)"""
    data = request.get_json()
    steam_id = data.get('steam_id')
    username = data.get('username', 'Debug User')
    
    session['steam_id'] = steam_id
    
    return jsonify({
        'success': True,
        'steam_id': steam_id,
        'message': 'Logged in (DEBUG MODE)'
    })

@app.route('/api/debug/players', methods=['GET'])
def debug_players():
    """DEBUG: Zobrazí všechny hráče"""
    return jsonify(players_positions)

# ============ HEALTH CHECK ============

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Změň debug=False v produkci!
    app.run(host='0.0.0.0', port=5000, debug=True)
