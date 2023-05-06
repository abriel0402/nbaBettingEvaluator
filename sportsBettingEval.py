from bs4 import BeautifulSoup
import requests


class Leg:
     def __init__(self, player, stat, last5HR, last10HR, vsOpponentHR, line):
          self.player = player
          self.stat = stat
          self.last5HR = last5HR
          self.last10HR = last10HR
          self.vsOpponentHR = vsOpponentHR
          self.line = line



SLIP = []

top20Lines = []


end = False

def displaySlip(SLIP):
    if (len(SLIP) == 0):
        print("Slip Empty")
    else:
        for leg in SLIP:
            print(leg)

def addLeg():
    pass
    






def displayMenu():
      print("-----Abriel's NBA Betting Evaluator-----")
      print("1. View Slip")
      print("2. Add Leg")
      print("3. Delete Leg")
      print("4. Clear Slip")
      print("5. View Lines")
      

      print("5. Exit Program")
      print("----------------------------------------")
      choice = int(input("Select an option (1-5): "))
      return choice

while(not end):
      
      choice = displayMenu()
      if choice == 5:
        end = True