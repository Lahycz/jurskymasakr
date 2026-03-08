from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
import requests
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)
app.secret_key = 'tvoj-tajny-klic' # Změň na silný klíč

# ===== STEAM AUTHENTICATION =====
STEAM_OPENID_URL = 'https://steamcommunity.com/openid'
STEAM_API_KEY = 'tvuj-steam-api-klic'  # Zvedni si z Steam Dev API

# In-memory storage
players = {}  # steam_id: {position, friends, last_update}
friends = {}  # steam_id: [friend_steam_id, ...]

# ===== ROUTES =====
@app.route('/api/login', methods=['GET'])
def steam_login():
    """Redirect to Steam OpenID login"""
    return redirect(f'{STEAM_OPENID_URL}?openid.ns=http://specs.openid.net/auth/2.0&openid.mode=checkid_setup&openid.return_to={request.host_url}api/verify&openid.identity=http://specs.openid.net/auth/2.0/identifier_select&openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select')

@app.route('/api/verify', methods=['GET'])
def verify_steam():
    """Verify Steam login and store session"""
    # Ověř Steam OpenID
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'check_auth',
    }
    params.update(request.args)
    
    response = requests.post(STEAM_OPENID_URL, data=params)
    
    if 'is_valid:true' in response.text:
        # Extrahuj Steam ID z identity
        steam_id = request.args.get('openid.identity', '').split('/')[-1]
        session['steam_id'] = steam_id
        
        # Inicializuj hráče
        if steam_id not in players:
            players[steam_id] = {
                'position': {'lat': 961.5, 'lng': 960},  # Spawn point
                'friends': [],
                'last_update': datetime.now().isoformat()
            }
        
        return redirect('/index.html')  # Přesměruj na mapu
    
    return jsonify({'error': 'Steam verification failed'}), 401

@app.route('/api/position', methods=['GET', 'POST'])
def handle_position():
    """Načti nebo aktualizuj pozici hráče"""
    steam_id = request.cookies.get('steam_id') or session.get('steam_id')
    
    if not steam_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        # Vrať pozici hráče
        if steam_id in players:
            return jsonify(players[steam_id]['position'])
        return jsonify({'lat': 961.5, 'lng': 960})
    
    # POST: Aktualizuj pozici
    data = request.get_json()
    if steam_id not in players:
        players[steam_id] = {
            'position': {'lat': 961.5, 'lng': 960},
            'friends': [],
            'last_update': datetime.now().isoformat()
        }
    
    players[steam_id]['position'] = data
    players[steam_id]['last_update'] = datetime.now().isoformat()
    
    return jsonify({'success': True})

@app.route('/api/friends/add', methods=['POST'])
def add_friend():
    """Přidej přítele"""
    steam_id = request.cookies.get('steam_id') or session.get('steam_id')
    data = request.get_json()
    friend_steam_id = data.get('friend_id')
    
    if not steam_id or not friend_steam_id:
        return jsonify({'error': 'Invalid input'}), 400
    
    if steam_id not in players:
        players[steam_id] = {
            'position': {'lat': 961.5, 'lng': 960},
            'friends': [],
            'last_update': datetime.now().isoformat()
        }
    
    if friend_steam_id not in players[steam_id]['friends']:
        players[steam_id]['friends'].append(friend_steam_id)
    
    return jsonify({'success': True})

@app.route('/api/friends/remove', methods=['POST'])
def remove_friend():
    """Odeber přítele"""
    steam_id = request.cookies.get('steam_id') or session.get('steam_id')
    data = request.get_json()
    friend_steam_id = data.get('friend_id')
    
    if steam_id in players and friend_steam_id in players[steam_id]['friends']:
        players[steam_id]['friends'].remove(friend_steam_id)
    
    return jsonify({'success': True})

@app.route('/api/friends/<steam_id>', methods=['GET'])
def get_friends(steam_id):
    """Vrať pozice přátel"""
    current_user = request.cookies.get('steam_id') or session.get('steam_id')
    
    if not current_user or current_user not in players:
        return jsonify({'error': 'Not authenticated'}), 401
    
    friend_positions = {}
    for friend_id in players[current_user]['friends']:
        if friend_id in players:
            friend_positions[friend_id] = players[friend_id]['position']
    
    return jsonify(friend_positions)

@app.route('/api/player/<steam_id>', methods=['GET'])
def get_player_info(steam_id):
    """Vrať info o hráči"""
    if steam_id in players:
        return jsonify({
            'steam_id': steam_id,
            'position': players[steam_id]['position'],
            'last_update': players[steam_id]['last_update']
        })
    
    return jsonify({'error': 'Player not found'}), 404

@app.route('/api/logout', methods=['GET'])
def logout():
    """Odhlášení"""
    session.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
