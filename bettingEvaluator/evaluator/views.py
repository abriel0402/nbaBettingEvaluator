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

OVER_DECISION = 62
UNDER_DECISION = 35



ptsLinesSite = cache.get('ptsLinesSite')
if ptsLinesSite is None:
    ptsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-points").text 
    ptsLinesSoup = BeautifulSoup(ptsLinesSite, "lxml")  
    playerTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-row-name") 
    lineTagsPoints = ptsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('ptsLinesSite', ptsLinesSite, timeout=120)

astLinesSite = cache.get('astLinesSite')
if astLinesSite is None:
    astsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-assists").text
    astsLinesSoup = BeautifulSoup(astsLinesSite, "lxml")
    playerTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-row-name")
    lineTagsAssists = astsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('astLinesSite', astLinesSite, timeout=120)

rebsLinesSite = cache.get('rebsLinesSite')
if rebsLinesSite is None:
    rebsLinesSite = requests.get("https://sportsbook.draftkings.com/nba-playoffs?category=player-rebounds").text
    rebsLinesSoup = BeautifulSoup(rebsLinesSite, "lxml")
    playerTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-row-name")
    lineTagsRebounds = rebsLinesSoup.find_all("span", class_="sportsbook-outcome-cell__line")
    cache.set('rebsLineSite', rebsLinesSite, timeout=120)








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



# Decides whether to go over, under, or pass
def getDecision(last5, last10, last20):

    
    average = 50
    numOfRates = 0
    if last5 != None:
        hitRate5 = int(last5[0][:-1])
        numOfRates += 1
    else:
        hitRate5 = 0
    if last10 != None:
        hitRate10 = int(last10[0][:-1])
        numOfRates += 1
    else:
        hitRate10 = 0
    if last20 != None:
        hitRate20 = int(last20[0][:-1])
        numOfRates += 1
    else:
        hitRate20 = 0
    
    if numOfRates > 0:
        average = (hitRate5 + hitRate10 + hitRate20)/numOfRates
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


class Leg:
    def __init__(self, player, stat, line, playerID, last5=[], last10=[], last20=[], season=[], decision=[]):
        self.player = player
        self.stat = stat
        self.line = line
        self.playerID = playerID
        self.decision = decision

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
    cache.set("POINTS_LEGS", POINTS_LEGS, timeout=120)
ASSISTS_LEGS = cache.get("ASSISTS_LEGS")
if ASSISTS_LEGS is None:
    ASSISTS_LEGS = createLegs(playerTagsAssists, filteredLineTagsAssists, "AST")
    cache.set("ASSISTS_LEGS", ASSISTS_LEGS, timeout=120)
    
REBOUNDS_LEGS = cache.get("REBOUNDS_LEGS")
if REBOUNDS_LEGS is None:
    REBOUNDS_LEGS = createLegs(playerTagsRebounds, filteredLineTagsRebounds, "REB")
    cache.set("REBOUNDS_LEGS", REBOUNDS_LEGS, timeout=120)


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
    cache.set("PA_LEGS", PA_LEGS, timeout=120)

PR_LEGS = cache.get("PR_LEGS")
if PR_LEGS is None:
    PR_LEGS = create2ComboLegs(POINTS_LEGS, REBOUNDS_LEGS, "PR")
    cache.set("PR_LEGS", PR_LEGS, timeout=120)

RA_LEGS = cache.get("RA_LEGS")
if RA_LEGS is None:
    RA_LEGS = create2ComboLegs(REBOUNDS_LEGS, ASSISTS_LEGS, "RA")
    cache.set("RA_LEGS", RA_LEGS, timeout=120)

#stat should be formatted as: PRA
def create3ComboLegs(LEGS1, LEGS2, LEGS3, stat):
    NEW_LEGS = []
    for leg1 in LEGS1:
        for leg2 in LEGS2:
            for leg3 in LEGS3:
                if leg3.player == leg2.player and leg3.player == leg1.player:
                    line = float(leg1.line)+float(leg2.line)+float(leg3.line)
                    legToAdd = Leg(leg1.player, stat, line, leg1.playerID)
                    
                    NEW_LEGS.append(legToAdd)
    return NEW_LEGS

PRA_LEGS = cache.get("PRA_LEGS")
if PRA_LEGS is None:
    PRA_LEGS = create3ComboLegs(POINTS_LEGS, REBOUNDS_LEGS, ASSISTS_LEGS, "PRA")
    cache.set("PRA_LEGS", PRA_LEGS, timeout=120)

#get hit rates
def getHitRates(leg, n, stat1="N/A", stat2="N/A", stat3="N/A"):
    lastN = []
    if leg.stat in ["PTS", "AST", "REB"]:
        x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(n)
        print("api being called")
        lastN = x[leg.stat].tolist()
        
        hitCount = 0
        # missingGames = n-len(lastN)

        # For playoffs 
        #   if missingGames != 0:
         #      print("api being called")
          #     x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
           #    missingGamesList = x[leg.stat].tolist()
            #   lastN = lastN + missingGamesList

        for stat in lastN:
            if float(stat) > float(leg.line):
                hitCount = hitCount + 1

        hitRateN = str(int((hitCount/len(lastN))*100))+"%"
        return [hitRateN, lastN]
        
    elif leg.stat in ["PA", "PR", "RA"]:
        print("api being called")
        x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(n)
        lastN1 = x[stat1].tolist()
        lastN2 = x[stat2].tolist()
        
        hitCount = 0
        missingGames = n-len(lastN1)
        
        # For playoffs
        #  if missingGames != 0:
          #     print("api being called")
           #    x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
            #   missingGamesList1 = x[stat1].tolist()
         #      missingGamesList2 = x[stat2].tolist()
          #     lastN1 = lastN1 + missingGamesList1
           #    lastN2 = lastN2 + missingGamesList2
        
        for i in range(len(lastN1)):
            lastN.append(lastN1[i]+lastN2[i])
            if (float(lastN1[i])+float(lastN2[i])) > float(leg.line):
                hitCount = hitCount + 1
        hitRateN = str(int((hitCount/len(lastN1))*100))+"%"
        return [hitRateN, lastN]
        
    else:
        print("api call")
        x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(n)
        # for playoffs: x = playergamelog.PlayerGameLog(leg.playerID, season_type_all_star="Playoffs").get_data_frames()[0].head(n)
        lastN1 = x[stat1].tolist()
        lastN2 = x[stat2].tolist()
        lastN3 = x[stat3].tolist()
        
        hitCount = 0
        missingGames = n-len(lastN1)

        # for playoffs

        #   if missingGames != 0:
         #       print("api being called")
          #     x = playergamelog.PlayerGameLog(leg.playerID).get_data_frames()[0].head(missingGames)
           #    missingGamesList1 = x[stat1].tolist()
          #     missingGamesList2 = x[stat2].tolist()
           #    missingGamesList3 = x[stat3].tolist()
           #    lastN1 = lastN1 + missingGamesList1
           #    lastN2 = lastN2 + missingGamesList2
           #    lastN3 = lastN3 + missingGamesList3
        for i in range(len(lastN1)):
            lastN.append(lastN1[i]+lastN2[i]+lastN3[i])
            if (float(lastN1[i])+float(lastN2[i])+float(lastN3[i]) > float(leg.line)):
                hitCount += 1
        hitRateN = str(int((hitCount/len(lastN))*100))+"%"
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

def pa(request):
    return render(request, "evaluator/pa.html", {
        "legs": PA_LEGS,
    })

def pr(request):
    return render(request, "evaluator/pr.html", {
        "legs": PR_LEGS,
    })

def ra(request):
    return render(request, "evaluator/ra.html", {
        "legs": RA_LEGS,
    })

def pra(request):
    
    return render(request, "evaluator/pra.html", {
        "legs": PRA_LEGS,
    })

def player(request, playerID, stat):
    
    
    
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
        stat1 = "PTS"
        stat2 = "AST"
    elif stat == "PR":
        CURR_LEGS = PR_LEGS
        statTxt = "pr"
        statPerGame = "prpg"
        stat1 = "PTS"
        stat2 = "REB"
    elif stat == "RA":
        CURR_LEGS = RA_LEGS
        statTxt = "ra"
        statPerGame = "rapg"
        stat1 = "REB"
        stat2 = "AST"
    elif stat == "PRA":
        CURR_LEGS = PRA_LEGS
        statTxt = "pra"
        statPerGame = "prapg"
        stat1 = "PTS"
        stat2 = "REB"
        stat3 = "AST"

    for leg in CURR_LEGS:
        if str(leg.playerID) == str(playerID):
            leg = leg
            break
    
    
    #  Hit Rates
    if leg.stat in ["PA", "PR", "RA"]:
        hitRates = getHitRates(leg, 20, stat1, stat2)
        leg.last20 = hitRates[1]
        hitRate20 = hitRates[0]
    

        hitRates = getHitRates(leg, 10, stat1, stat2)
        leg.last10 = hitRates[1]
        hitRate10 = hitRates[0]

        hitRates = getHitRates(leg, 5, stat1, stat2)
        leg.last5 = hitRates[1]
        hitRate5 = hitRates[0]

        #Get Season Hit Rate
        hitCount = 0
        print("api being called")

        # For this line below, make sure it is the correct season
        x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
        list1 = x[stat1].tolist()
        list2 = x[stat2].tolist()
        for i in range(len(list1)):
            if float(list1[i]+list2[i]) > float(leg.line):
                hitCount = hitCount + 1
        hitRateSzn = str(int((hitCount/len(list1))*100))+"%"
    elif leg.stat in ["PTS", "REB", "AST"]: 
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
        print("api being called")
        hitCount = 0
        x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
        leg.season = x[leg.stat].tolist()
        for stat in leg.season:
            if float(stat) > float(leg.line):
               hitCount = hitCount + 1
        hitRateSzn = str(int((hitCount/len(leg.season))*100))+"%"
    else:
        hitRates = getHitRates(leg, 20, stat1, stat2, stat3)
        leg.last20 = hitRates[1]
        hitRate20 = hitRates[0]
    

        hitRates = getHitRates(leg, 10, stat1, stat2, stat3)
        leg.last10 = hitRates[1]
        hitRate10 = hitRates[0]

        hitRates = getHitRates(leg, 5, stat1, stat2, stat3)
        leg.last5 = hitRates[1]
        hitRate5 = hitRates[0]

        #Get Season Hit Rate
        hitCount = 0
        print("api being called")
        x = playergamelog.PlayerGameLog(leg.playerID, season="2022").get_data_frames()[0]
        list1 = x[stat1].tolist()
        list2 = x[stat2].tolist()
        list3 = x[stat3].tolist()
        for i in range(len(list1)):
            if float(list1[i]+list2[i]+list3[i]) > float(leg.line):
                hitCount = hitCount + 1
        hitRateSzn = str(int((hitCount/len(list1))*100))+"%"
    

    
        
    # Get Averages
    total = 0
    if leg.last5 != None:
        for stat in leg.last5:
            total = total + stat
        average5 = round((total/5), 1)
        total = 0
    if leg.last10 != None:
        for stat in leg.last10:
            total = total + stat
        average10 = round((total/10), 1)
        total = 0
    if leg.last20 != None:
        for stat in leg.last20:
            total = total + stat
        average20 = round((total/20), 1)
        total = 0
    if leg.stat in ["PTS", "AST", "REB"]:
        for stat in leg.season:
            total = total + stat
        averageSeason = round((total/len(leg.season)), 1)
    elif leg.stat in ["PR", "PA", "RA"]:
        for i in range(len(list1)):
            total += list1[i] + list2[i]
        averageSeason = round((total/len(list1)), 1)
    else:
        for i in range(len(list1)):
            total += list1[i] + list2[i] + list3[i]
        averageSeason = round((total/len(list1)), 1)

    if leg.stat in ["PTS", "AST", "REB"]:
        hitRates = [getHitRates(leg, n) for n in [5, 10, 20]]
    elif leg.stat in ["PR", "PA", "RA"]:
        hitRates = [getHitRates(leg, n, stat1, stat2) for n in [5, 10, 20]]
    else:
        hitRates = [getHitRates(leg, n, stat1, stat2, stat3) for n in [5, 10, 20]]
    decisionList = getDecision(*hitRates)
    decision = decisionList[0]
    color = decisionList[1]
    

    

    return render(request, "evaluator/player.html", {
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
    #cache.set(CACHE_KEY, response, settings.CACHE_TTL)
    #return response