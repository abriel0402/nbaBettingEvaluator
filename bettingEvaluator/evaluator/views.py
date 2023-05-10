from django.shortcuts import render
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll


ptsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-points").text
ptsLinesSoup = BeautifulSoup(ptsLinesSite, "lxml")

playerTags = ptsLinesSoup.find_all("span", class_="sportsbook-row-name")
lineTags = ptsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")

fixedLineTags = []

PLAYERS = players.get_players()

addCurrent = True
for tag in lineTags:
    if addCurrent:
        fixedLineTags.append(tag)
        addCurrent = False
    elif not addCurrent:
        addCurrent = True

LEGS = []

class Leg:
    def __init__(self, player, stat, line, playerID, last5=[], last10=[], last20=[], season=0, vsOpp=[]):
        self.player = player
        self.stat = stat
        self.line = line
        self.playerID = playerID

for i in range(len(playerTags)):
    for player in PLAYERS:
        if player["full_name"] == playerTags[i].text:
            playerID = player["id"]
            
            

    legToAdd = Leg(playerTags[i].text, "pts", fixedLineTags[i].text, playerID)
    LEGS.append(legToAdd)








# Create your views here.
def index(request):
    return render(request, "evaluator/index.html", {
        "legs": LEGS,
    })

def player(request, playerID):
    
    for leg in LEGS:
        if str(leg.playerID) == str(playerID):
            leg = leg
            break

    return render(request, "evaluator/player.html", {
        "leg": leg,
    })