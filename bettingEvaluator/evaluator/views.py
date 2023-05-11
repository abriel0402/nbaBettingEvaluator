from django.shortcuts import render
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog


PLAYERS = players.get_players()

ptsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-points").text
astsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-assists").text
rebsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-rebounds").text

ptsLinesSoup = BeautifulSoup(ptsLinesSite, "lxml")
astsLinesSoup = BeautifulSoup(astsLinesSite, "lxml")
rebsLinesSoup = BeautifulSoup(rebsLinesSite, "lxml")

playerTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-row-name")
playerTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-row-name")
playerTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-row-name")

lineTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
lineTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
lineTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")






def filterTags(lineTags):
    filtered = []
    addCurrent = True
    for tag in lineTags:
        if addCurrent:
            filtered.append(tag)
            addCurrent = False
        elif not addCurrent:
            addCurrent = True
    return filtered

filteredLineTagsPoints = filterTags(lineTagsPoints)
filteredLineTagsAssists = filterTags(lineTagsAssists)
filteredLineTagsRebounds = filterTags(lineTagsRebounds)


class Leg:
    def __init__(self, player, stat, line, playerID, last5=[], last10=[], last20=[], season=[], vsOpp=[]):
        self.player = player
        self.stat = stat
        self.line = line
        self.playerID = playerID

#get legs
def createLegs(playerTags, filteredLineTags, stat):
    LEGS = []
    for i in range(len(playerTags)):
        for player in PLAYERS:
            if player["full_name"] == playerTags[i].text:
                playerID = player["id"]
            
        legToAdd = Leg(playerTags[i].text, stat, filteredLineTags[i].text, playerID)
        LEGS.append(legToAdd)
    return LEGS


POINTS_LEGS = createLegs(playerTagsPoints, filteredLineTagsPoints, "PTS")
ASSISTS_LEGS = createLegs(playerTagsAssists, filteredLineTagsAssists, "AST")
REBOUNDS_LEGS = createLegs(playerTagsRebounds, filteredLineTagsRebounds, "REB")

#get hit rates
def getHitRates(leg, n):
    x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(n)
    lastN = x[leg.stat].tolist()
    hitCount = 0
    missingGames = n-len(lastN)
    if missingGames != 0:
        x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
        missingGamesList = x[leg.stat].tolist()
        lastN = lastN + missingGamesList
    for stat in lastN:
        if float(stat) > float(leg.line):
            hitCount = hitCount + 1
    
    hitRateN = str(int((hitCount/n)*100))+"%"
    return [hitRateN, lastN]


# Create your views here.
def index(request):
    return render(request, "evaluator/index.html", {
    })

def points(request):
    return render(request, "evaluator/points.html", {
        "legs": POINTS_LEGS,
    })

def assists(request):
    return render(request, "evaluator/assists.html", {
        "legs": ASSISTS_LEGS,
    })

def rebounds(request):
    return render(request, "evaluator/rebounds.html", {
        "legs": REBOUNDS_LEGS,
    })

def player(request, playerID, stat):
    if stat == "PTS":
        for leg in POINTS_LEGS:
            if str(leg.playerID) == str(playerID):
                leg = leg
                statTxt = "pts"
                break
    if stat == "AST":
        for leg in ASSISTS_LEGS:
            if str(leg.playerID) == str(playerID):
                leg = leg
                statTxt = "asts"
                break
    if stat == "REB":
        for leg in REBOUNDS_LEGS:
            if str(leg.playerID) == str(playerID):
                leg = leg
                statTxt = "rebs"
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

    #Get Season Hit Rate
    hitCount = 0
    x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
    leg.season = x[leg.stat].tolist()
    for stat in leg.season:
        if float(stat) > float(leg.line):
            hitCount = hitCount + 1
    hitRateSzn = str(int((hitCount/len(leg.season))*100))+"%"
        

    return render(request, "evaluator/player.html", {
        "leg": leg,
        "hitRate5": hitRate5,
        "hitRate10": hitRate10,
        "hitRate20": hitRate20,
        "hitRateSzn": hitRateSzn,
        "stat": statTxt,
    })
