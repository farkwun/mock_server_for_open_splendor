import csv

ID = 'id'
PRESTIGE = 'prestige'
TYPE = 'type'
RED = 'red'
GREEN = 'green'
BLUE = 'blue'
WHITE = 'white'
BLACK = 'black'


COLOR_KEYS = {RED, GREEN, BLUE, WHITE, BLACK}

class Card(object):
    def __init__(self, dict):
        self.id = dict[ID]
        self.prestige = dict[PRESTIGE]
        self.type = dict[TYPE]
        self.costs = self.get_costs_from(dict)
    
    def get_costs_from(self, dict):
        costs = {}
        for key in COLOR_KEYS:
            if int(dict[key]) != 0:
                costs[key] = dict[key]
        return costs

    def print(self):
        print("'" + self.id +"',")


with open('cards.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    print("LEVEL_THREE = {")
    for row in reader:
        if int(row['level']) == 3:
            card = Card(row)
            card.print()
    print("}")
