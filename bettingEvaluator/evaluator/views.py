from django.conf import settings
from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse
from bs4 import BeautifulSoup
import requests
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import *



PLAYERS = cache.get("PLAYERS")
if PLAYERS is None:
    PLAYERS = players.get_players()
    cache.set("PLAYERS", PLAYERS, timeout=60*60*24*7)

OVER_DECISION = 66
UNDER_DECISION = 32



ptsLinesSite = cache.get('ptsLinesSite')
if ptsLinesSite is None:
    ptsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-points").text 
    ptsLinesSoup = BeautifulSoup(ptsLinesSite, "lxml")  
    playerTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-row-name") 
    lineTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('ptsLinesSite', ptsLinesSite, timeout=300)

astLinesSite = cache.get('astLinesSite')
if astLinesSite is None:
    astsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-assists").text
    astsLinesSoup = BeautifulSoup(astsLinesSite, "lxml")
    playerTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-row-name")
    lineTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('astLinesSite', astLinesSite, timeout=300)

rebsLinesSite = cache.get('rebsLinesSite')
if rebsLinesSite is None:
    rebsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-rebounds").text
    rebsLinesSoup = BeautifulSoup(rebsLinesSite, "lxml")
    playerTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-row-name")
    lineTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('rebsLineSite', rebsLinesSite, timeout=300)








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

POINTS_LEGS = cache.get("POINTS_LEGS")
if POINTS_LEGS is None:
    POINTS_LEGS = createLegs(playerTagsPoints, filteredLineTagsPoints, "PTS")
    cache.set("POINTS_LEGS", POINTS_LEGS, timeout=300)
ASSISTS_LEGS = cache.get("ASSISTS_LEGS")
if ASSISTS_LEGS is None:
    ASSISTS_LEGS = createLegs(playerTagsAssists, filteredLineTagsAssists, "AST")
    cache.set("ASSISTS_LEGS", ASSISTS_LEGS, timeout=300)
    
REBOUNDS_LEGS = cache.get("REBOUNDS_LEGS")
if REBOUNDS_LEGS is None:
    REBOUNDS_LEGS = createLegs(playerTagsRebounds, filteredLineTagsRebounds, "REB")
    cache.set("REBOUNDS_LEGS", REBOUNDS_LEGS, timeout=300)


#stat should be formatted as: PR, PA, RA, SB
def create2ComboLegs(LEGS1, LEGS2, stat):
    NEW_LEGS = []
    for leg1 in LEGS1:
        curr = leg1.player
        for leg2 in LEGS2:
            if leg2.player == curr:
                line = round((float(leg1.line)+float(leg2.line)+0.5), 1)
                legToAdd = Leg(leg1.player, stat, line, leg1.playerID)
                NEW_LEGS.append(legToAdd)
    return NEW_LEGS

PA_LEGS = cache.get("PA_LEGS")
if PA_LEGS is None:
    PA_LEGS = create2ComboLegs(POINTS_LEGS, ASSISTS_LEGS, "PA")
    cache.set("PA_LEGS", PA_LEGS, timeout=300)
#get hit rates
def getHitRates(leg, n, stat1="N/A", stat2="N/A"):
    lastN = []
    if leg.stat in ["PTS", "AST", "REB"]:
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
    else:
        x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(n)
        lastN1 = x[stat1].tolist()
        x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(n)
        lastN2 = x[stat2].tolist()
        hitCount = 0
        missingGames = n-len(lastN1)
        if missingGames != 0:
            x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
            missingGamesList1 = x[stat1].tolist()
            x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
            missingGamesList2 = x[stat2].tolist()
            lastN1 = lastN1 + missingGamesList1
            lastN2 = lastN2 + missingGamesList2
        
        for i in range(len(lastN1)):
            lastN.append(lastN1[i]+lastN2[i])
            if (float(lastN1[i])+float(lastN2[i])) > float(leg.line):
                hitCount = hitCount + 1
        hitRateN = str(int((hitCount/n)*100))+"%"
        return [hitRateN, lastN]




# Decides whether to go over, under, or pass
def getDecision(last5, last10, last20):

    hitRate5 = int(last5[0][:-1])
    hitRate10 = int(last10[0][:-1])
    hitRate20 = int(last20[0][:-1])
    average = (hitRate5 + hitRate10 + hitRate20)/3
    if average >= OVER_DECISION:
        decision = "OVER"
        color = "btn btn-success"
    elif average <= UNDER_DECISION:
        decision = "UNDER"
        color = "btn btn-danger"
    else:
        decision = "PASS"
        color = "btn btn-dark"
    return [decision, color]




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

def pa(request):
    return render(request, "evaluator/pa.html", {
        "legs": PA_LEGS,
    })


def player(request, playerID, stat):

    CACHE_KEY = str(playerID) + ":" + stat
    CACHED_DATA = cache.get(CACHE_KEY)
    if CACHED_DATA:
        return CACHED_DATA
    
    if stat == "PTS":
        CURR_LEGS = POINTS_LEGS
        statTxt = "pts"
        statPerGame = "ppg"
    elif stat == "AST":
        CURR_LEGS = ASSISTS_LEGS
        statTxt = "asts"
        statPerGame = "apg"
    elif stat == "REB":
        CURR_LEGS = REBOUNDS_LEGS
        statTxt = "rebs"
        statPerGame = "rpg"
    elif stat == "PA":
        CURR_LEGS = PA_LEGS
        statTxt = "pa"
        statPerGame = "papg"

    for leg in CURR_LEGS:
        if str(leg.playerID) == str(playerID):
            leg = leg
            break
    
    
    #  Hit Rates
    if leg.stat == "PA":
        hitRates = getHitRates(leg, 20, "PTS", "AST")
        leg.last20 = hitRates[1]
        hitRate20 = hitRates[0]
    

        hitRates = getHitRates(leg, 10, "PTS", "AST")
        leg.last10 = hitRates[1]
        hitRate10 = hitRates[0]

        hitRates = getHitRates(leg, 5, "PTS", "AST")
        leg.last5 = hitRates[1]
        hitRate5 = hitRates[0]

        #Get Season Hit Rate
        hitCount = 0
        x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
        list1 = x["PTS"].tolist()
        x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
        list2 = x["AST"].tolist()
        for i in range(len(list1)):
            if float(list1[i]+list2[i]) > float(leg.line):
                hitCount = hitCount + 1
        hitRateSzn = str(int((hitCount/len(list1))*100))+"%"
    else: 
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

    

    
        
    # Get Averages
    total = 0
    for stat in leg.last5:
        total = total + stat
    average5 = round((total/5), 1)
    total = 0
    for stat in leg.last10:
        total = total + stat
    average10 = round((total/10), 1)
    total = 0
    for stat in leg.last20:
        total = total + stat
    average20 = round((total/20), 1)
    total = 0
    if leg.stat in ["PTS", "AST", "REB"]:
        for stat in leg.season:
            total = total + stat
        averageSeason = round((total/len(leg.season)), 1)
    elif leg.stat == "PA":
        for i in range(len(list1)):
            total += list1[i] + list2[i]
        averageSeason = round((total/len(list1)), 1)

    if leg.stat in ["PTS", "AST", "REB"]:
        hitRates = [getHitRates(leg, n) for n in [5, 10, 20]]
    elif leg.stat == "PA":
        hitRates = [getHitRates(leg, n, "PTS", "AST") for n in [5, 10, 20]]
    decisionList = getDecision(*hitRates)
    decision = decisionList[0]
    color = decisionList[1]
    

    response = render(request, "evaluator/player.html", {
        "leg": leg,
        "hitRate5": hitRate5,
        "hitRate10": hitRate10,
        "hitRate20": hitRate20,
        "hitRateSzn": hitRateSzn,
        "stat": statTxt,
        "statPerGame": statPerGame,
        "average5": average5,
        "average10": average10,
        "average20": average20,
        "averageSeason": averageSeason,
        "decision": decision,
        "color": color,

    })
    cache.set(CACHE_KEY, response, settings.CACHE_TTL)
    return response