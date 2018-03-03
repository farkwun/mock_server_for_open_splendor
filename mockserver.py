from flask import Flask, jsonify, request, Response
import json
import random
import pdb

from cards import CARDS
from nobles import NOBLES

class MockDB(object):
    def __init__(self):
        self.GAMES = {}

    def gen_id(self):
        id = ""
        while len(id) < ID_LEN:
            id += random.choice(LETTERS)
        return id

    def add_game(self, username):
        new_id = self.gen_id()
        while new_id in self.GAMES:
            new_id = self.gen_id()
        self.GAMES[new_id] = Game(username, new_id)
        return new_id

class Game(object):
    def __init__(self, user, roomId):
        self.players = {user: Player(user)}
        self.roomId = roomId
        self.active = False
        self.nobleList = []
        self.levels = []
        self.coins = {}
        self.roundNum = 1
        self.playOrder = [user]
        self.playIndex = 0

    def to_dict(self):
        return {
            "roomId" : self.roomId,
            "players" : self.create_player_object(),
            "active": self.active,
            "nobleList": self.nobleList,
            "levels": self.levels,
            "coins": self.coins,
            "roundNum": self.roundNum,
            "playOrder": self.playOrder,
            "playIndex": self.playIndex
        }
    
    def add_player(self, username):
        self.players[username] = Player(username)
        self.playOrder.append(username)
    
    def create_player_object(self):
        p_object = {}
        for username, player in self.players.items():
            p_object[username] = player.to_dict()
        return p_object

    def activate(self):
        self.active = True


class Player(object):
    ID = "id"
    PRESTIGE = "prestige"
    COINS = "coins"
    CARDS = "cards"
    NOBLES = "nobles"
    def __init__(self, username):
        self.username = username
        self.prestige = 0
        self.coins = {}
        self.cards = []
        self.nobles = []

    def to_dict(self):
        return {
            self.ID : self.username,
            self.PRESTIGE : self.prestige,
            self.COINS: self.coins,
            self.CARDS: self.cards,
            self.NOBLES: self.nobles,
        }

#@app.route('/', methods=['GET'])
#def index():
#    resp = jsonify({"message": "Hello Victor"})
#    resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
#    return resp

app = Flask(__name__)

LETTERS ='abcdefghijklmnopqrstuvwxyz'
ID_LEN = 6

DB = MockDB()

@app.route('/game', methods=['GET'])
def poll():
    game_id = request.args.get('roomId')
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/game', methods=['POST'])
def update():
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = content['roomId']
    DB.GAMES[game_id].activate()
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/join', methods=['POST'])
def join():
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = content['roomId']
    new_user = content['user']
    DB.GAMES[game_id].add_player(new_user)
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/new', methods=['POST'])
def newgame():
#    pdb.set_trace()
    print("hELO")
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = DB.add_game(content['user'])
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == "__main__":
    app.run(debug=True)

