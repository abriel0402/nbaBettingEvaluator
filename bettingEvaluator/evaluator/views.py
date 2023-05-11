from django.shortcuts import render
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.library.parameters import SeasonAll
import json.decoder
import time


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
    def __init__(self, player, stat, line, playerID, last5=[], last10=[], last20=[], season=[], vsOpp=[]):
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


def getHitRates(leg, n):
    x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(n)
    lastN = x["PTS"].tolist()
    hitCount = 0
    missingGames = n-len(lastN)
    if missingGames != 0:
        x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
        missingGamesList = x["PTS"].tolist()
        lastN = lastN + missingGamesList
    for pts in lastN:
        if float(pts) > float(leg.line):
            hitCount = hitCount + 1
    
    hitRateN = str(int((hitCount/n)*100))+"%"
    return [hitRateN, lastN]


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
    
    

    hitRates = getHitRates(leg, 20)
    leg.last20 = hitRates[1]
    hitRate20 = hitRates[0]

    hitRates = getHitRates(leg, 10)
    leg.last10 = hitRates[1]
    hitRate10 = hitRates[0]

    hitRates = getHitRates(leg, 5)
    leg.last5 = hitRates[1]
    hitRate5 = hitRates[0]


    hitCount = 0
    #Get Season Hit Rate
    x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
    leg.season = x["PTS"].tolist()
    for pts in leg.season:
        if float(pts) > float(leg.line):
            hitCount = hitCount + 1
    hitRateSzn = str(int((hitCount/len(leg.season))*100))+"%"
        

    return render(request, "evaluator/player.html", {
        "leg": leg,
        "hitRate5": hitRate5,
        "hitRate10": hitRate10,
        "hitRate20": hitRate20,
        "hitRateSzn": hitRateSzn,
    })