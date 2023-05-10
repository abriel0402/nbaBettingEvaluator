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
    
    #Get Last 5 and 10 Hit Rates (PLAYOFFS)
    x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(5)
    leg.last5 = x["PTS"].tolist()
    x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(10)
    leg.last10 = x["PTS"].tolist()
    
    hitCount = 0
    for pts in leg.last5:
        if float(pts) > float(leg.line):
            hitCount = hitCount + 1
    hitRate5 = str(int((hitCount/5)*100))+"%"
    for pts in leg.last10:
        if float(pts) > float(leg.line):
            hitCount = hitCount + 1
    hitRate10 = str(int((hitCount/10)*100))+"%"

    #Get Last 20 Hit Rate (PLAYOFFS)
    x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(20)
    leg.last20 = x["PTS"].tolist()
    for pts in leg.last20:
        if float(pts) > float(leg.line):
            hitCount = hitCount + 1
    #missingGames = 20-len(leg.last20)
    #if missingGames != 0:
        #x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0].head(missingGames)
        #leg.last20 = x["PTS"].tolist()


    hitRate20 = str(int((hitCount/20)*100))+"%"



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