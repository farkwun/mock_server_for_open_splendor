import csv

ID = 'id'
PRESTIGE = 'prestige'
RED = 'red'
GREEN = 'green'
BLUE = 'blue'
WHITE = 'white'
BLACK = 'black'


COLOR_KEYS = {RED, GREEN, BLUE, WHITE, BLACK}

class Noble(object):
    def __init__(self, dict):
        self.id = dict[ID]
        self.prestige = dict[PRESTIGE]
        self.costs = self.get_costs_from(dict)
    
    def get_costs_from(self, dict):
        costs = {}
        for key in COLOR_KEYS:
            if int(dict[key]) != 0:
                costs[key] = dict[key]
        return costs

    def print(self):
        print("'" + self.id +"'" + ": " + "{")
        print("'id': '" + self.id + "',")
        print("'prestige': " + self.prestige+ ",")
        print("'costs': {")
        for key, value in self.costs.items():
            print("'" +key + "': " + value + ",")
        print("},")
        print("'imgURL': 'https://cf.geekdo-images.com/A_GXbAh-oYSAOGOVYFXPAHvfezU=/fit-in/1200x630/pic2803135.jpg'")
        print("},")


with open('nobles.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    print("NOBLES = {")
    for row in reader:
        noble = Noble(row)
        noble.print()
    print("}")
