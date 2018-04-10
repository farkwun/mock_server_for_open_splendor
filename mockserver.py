from flask import Flask, jsonify, request, Response, send_from_directory
import json
import random
import pdb
from functools import reduce

from cards import CARDS
from nobles import NOBLES

from levels import LEVEL_ONE, LEVEL_TWO, LEVEL_THREE

GREEN = "green"
RED = "red"
BLUE = "blue"
WHITE = "white"
BLACK = "black"
YELLOW = "yellow"

LEVELS = [LEVEL_ONE, LEVEL_TWO, LEVEL_THREE]

CARD_IDS = set()
NOBLE_IDS = set()

for card in CARDS.keys():
    CARD_IDS.add(card)

for noble in NOBLES.keys():
    NOBLE_IDS.add(noble)

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

class Level(object):
    def __init__(self, id):
        self.id = id
        self.rowCards = []
        self.deck = set(LEVELS[id-1])
        self.deal()

    def deal(self):
        self.rowCards = random.sample(self.deck, 4)
        for card in self.rowCards:
            self.deck.remove(card)

    def has_card(self, id):
        return id in self.rowCards
    
    def replace(self, id):
        for idx, card_id in enumerate(self.rowCards):
            if card_id == id:
                self.rowCards[idx] = self.get_card_from_deck()

    def get_card_from_deck(self):
        card_id = None
        if self.deck:
            [card_id] = random.sample(self.deck, 1)
            print(card_id)
            self.deck.remove(card_id)
        return card_id

    def to_dict(self):
        return{
            "id": str(self.id),
            "rowCards": self.rowCards
        }


class Game(object):
    def __init__(self, user, roomId):
        self.players = {user: Player(user)}
        self.roomId = roomId
        self.active = False
        self.nobleList = []
        self.levels = []
        self.coins = {
            GREEN: 7,
            BLUE: 7,
            RED: 7,
            WHITE: 7,
            BLACK: 7,
            YELLOW: 5,
        }
        self.roundNum = 1
        self.playOrder = [user]
        self.playIndex = 0

        self.cards_left = CARD_IDS
        self.winner = ""

    def to_dict(self):
        return {
            "roomId" : self.roomId,
            "players" : self.create_player_object(),
            "active": self.active,
            "nobleList": self.nobleList,
            "levels": list(map(lambda level: level.to_dict(), self.levels)),
            "coins": self.coins,
            "roundNum": self.roundNum,
            "playOrder": self.playOrder,
            "playIndex": self.playIndex,
            "winner": self.winner,
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
        self.nobleList = random.sample(NOBLE_IDS, 3 + len(self.players) - 2)
        self.levels = [Level(x) for x in reversed(range(1,4))]
        self.set_coins()

    def set_coins(self):
        if len(self.players) == 3:
            for coin in self.coins:
                self.coins[coin] -= 2
        elif len(self.players) == 2:
            for coin in self.coins:
                self.coins[coin] -= 3

    def check_winner(self):
        PRESTIGE = 0
        NUM_CARDS = 1
        USERNAME = 2
        best_player = sorted(map(
            lambda player: 
            (
                player.prestige,
                len(player.cards), 
                player.username
            ), 
            self.players.values()))[-1]

        if best_player[PRESTIGE] >= 15:
            self.winner = best_player[USERNAME]


    def increment_turn(self):
        self.playIndex += 1
        if self.playIndex >= len(self.playOrder):
            self.roundNum += 1
            self.playIndex = 0
            self.check_winner()

    def add_coins_to_player(self, coins, player_id):
        player = self.players[player_id]
        for coin in coins:
            type = coin['type']
            if type in player.coins:
                player.coins[type] += 1
            else:
                player.coins[type] = 1
            self.coins[type] -= 1
        self.increment_turn()

    def add_coins(self, coin, val):
        self.coins[coin] += val

    def add_jokers(self, val):
        self.coins[YELLOW] += val

    def buy_card_for_player(self, card_id, player_id):
        player = self.players[player_id]
        print("Bonuses:", player.get_bonuses())
        effective_cost = self.get_effective_cost(CARDS[card_id]['costs'], 
                                                 player.get_bonuses())
        print("Cost:", effective_cost)
        self.remove_coins_from_player(effective_cost, player_id)
        self.replace_card(card_id)
        self.noble_check(player_id)
        player.add_card(card_id)
        self.increment_turn()

    def buy_reserved_card_for_player(self, card_id, player_id):
        player = self.players[player_id]
        if card_id not in player.reserved:
            return
        player.add_card(card_id)
        effective_cost = self.get_effective_cost(CARDS[card_id]['costs'], 
                                                 player.get_bonuses())
        self.remove_coins_from_player(effective_cost, player_id)
        player.remove_reserved(card_id)
        self.noble_check(player_id)
        self.increment_turn()

    def reserve_card_for_player(self, card_id, player_id):
        player = self.players[player_id]
        player.reserve_card(card_id)
        self.replace_card(card_id)
        self.increment_turn()
        if (player.get_num_coins()+1) < 10 and self.coins[YELLOW] > 0:
            self.coins[YELLOW] -= 1
            player.add_coins(YELLOW, 1)

    def noble_check(self, player_id):
        bonuses = self.players[player_id].get_bonuses()
        for idx, noble_id in enumerate(self.nobleList):
            if not noble_id:
                continue
            costs = dict(NOBLES[noble_id]['costs'])
            for bonus, val in bonuses.items():
                if bonus in costs:
                    costs[bonus] -= val
                    if costs[bonus] <= 0:
                        costs.pop(bonus, None)
            if not costs:
                self.players[player_id].add_noble(noble_id)
                self.nobleList[idx] = None
                return
                
    def get_effective_cost(self, costs, bonuses):
        new_costs = dict(costs)
        for cost in costs.keys():
            if cost in bonuses:
                new_costs[cost] = max(0, costs[cost] - bonuses[cost])
            
            if new_costs[cost] == 0:
                new_costs.pop(cost, None)

        return new_costs

    def remove_coins_from_player(self, costs, player_id):
        player = self.players[player_id]
        for coin, val in costs.items():
            print(costs, player.coins, coin, val)
            joker_costs = 0
            if coin not in player.coins:
                joker_costs = val
            else:
                self.add_coins(coin, min(val, player.coins[coin]))
                joker_costs = max(val - player.coins[coin], 0)
                player.coins[coin] = max(player.coins[coin] - val, 0)
                if player.coins[coin] == 0:
                    player.coins.pop(coin, None)
            if YELLOW in player.coins:
                player.coins[YELLOW] -= joker_costs
                self.add_jokers(joker_costs)
                if player.coins[YELLOW] == 0:
                    player.coins.pop(YELLOW, None)

    def replace_card(self, card_id):
        for level in self.levels:
            if level.has_card(card_id):
                level.replace(card_id)

class Player(object):
    ID = "id"
    PRESTIGE = "prestige"
    COINS = "coins"
    CARDS = "cards"
    RESERVED = "reserved"
    NOBLES = "nobles"
    def __init__(self, username):
        self.username = username
        self.prestige = 0
        self.coins = {}
        self.cards = []
        self.reserved = []
        self.nobles = []

    def add_noble(self, noble_id):
        self.nobles.append(noble_id)
        self.update_prestige()

    def get_num_coins(self):
        return sum(self.coins.values())
    
    def add_coins(self, type, val):
        if type in self.coins:
            self.coins[type] += val
        else:
            self.coins[type] = val

    def add_card(self, card_id):
        self.cards.append(card_id)
        self.update_prestige()

    def reserve_card(self, card_id):
        self.reserved.append(card_id)

    def remove_reserved(self, card_id):
        print("Removing card: " + card_id, self.reserved)
        self.reserved.remove(card_id)
        print("Net reserved", self.reserved)

    def update_prestige(self):
        prestige = 0
        for noble_id in self.nobles:
            prestige += NOBLES[noble_id]['prestige']
        for card_id in self.cards:
            prestige += CARDS[card_id]['prestige']
        self.prestige = prestige

    def to_dict(self):
        return {
            self.ID : self.username,
            self.PRESTIGE : self.prestige,
            self.COINS: self.coins,
            self.CARDS: self.cards,
            self.RESERVED: self.reserved,
            self.NOBLES: self.nobles,
        }
    
    def increment_dict_by_val(self, dict, val):
        if val in dict:
            dict[val] += 1
        else:
            dict[val] = 1
        return dict

    def get_bonuses(self):
        return reduce(
            lambda bonuses, card_id: 
            self.increment_dict_by_val(bonuses, CARDS[card_id][TYPE]), 
            self.cards, 
            {})
    
#@app.route('/', methods=['GET'])
#def index():
#    resp = jsonify({"message": "Hello Victor"})
#    resp.headers.add('Access-Control-Allow-Origin', 'http://localhost:8080')
#    return resp

# POST TYPES
ACTIVATE = "activate"
MOVE = "move"
STASH = "stash"
CARD = "card"
ME = "me"

MOVE_TAKE_COINS = "take_coins"
MOVE_BUY_CARD = "buy_card"
MOVE_RESERVE_CARD = "reserve_card"
MOVE_BUY_RESERVED_CARD = "buy_reserved_card"

def parse_request(content, games):
    type = content[TYPE]
    game = games[content[ROOM_ID]]

    def parse_move(move):
        player_id = move[ME]
        move_type = move[MOVE]
        
        if move_type == MOVE_TAKE_COINS:
            game.add_coins_to_player(move[STASH], player_id)
        elif move_type == MOVE_BUY_CARD:
            game.buy_card_for_player(move[CARD], player_id)
        elif move_type == MOVE_RESERVE_CARD:
            game.reserve_card_for_player(move[CARD], player_id)
        elif move_type == MOVE_BUY_RESERVED_CARD:
            game.buy_reserved_card_for_player(move[CARD], player_id)

        print(game.players[player_id].get_bonuses())
        print(game.to_dict())

    if type == ACTIVATE: game.activate()
    elif type == MOVE:
        parse_move(content)

app = Flask(__name__)

LETTERS ='abcdefghijklmnopqrstuvwxyz'
ID_LEN = 6
TYPE = 'type'
ROOM_ID = 'roomId'

DB = MockDB()

@app.route('/api/game', methods=['GET'])
def poll():
    game_id = request.args.get('roomId')
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    return resp

@app.route('/api/game', methods=['POST'])
def update():
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = content[ROOM_ID]
    parse_request(content, DB.GAMES)
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    return resp

@app.route('/api/join', methods=['POST'])
def join():
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = content['roomId']
    new_user = content['user']
    if len(DB.GAMES[game_id].players) >= 4 or new_user in DB.GAMES[game_id].players:
        return 404

    DB.GAMES[game_id].add_player(new_user)
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    return resp

@app.route('/api/new', methods=['POST'])
def newgame():
#    pdb.set_trace()
    print("hELO")
    content = json.loads(request.get_data().decode(encoding='UTF-8'))
    print(content)
    game_id = DB.add_game(content['user'])
    resp = Response(json.dumps(DB.GAMES[game_id].to_dict()))
    return resp

if __name__ == "__main__":
    app.run(debug=True)

