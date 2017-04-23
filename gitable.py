#  gitabel
#  the world's smallest project management tool
#  reports relabelling times in github (time in seconds since epoch)
#  thanks to dr parnin
#  todo:
#    - ensure events sorted by time
#    - add issue id
#    - add person handle

"""
You will need to add your authorization token in the code.
Here is how you do it.

1) In terminal run the following command

curl -i -u <your_username> -d '{"scopes": ["repo", "user"], "note": "OpenSciences"}' https://api.github.com/authorizations

2) Enter ur password on prompt. You will get a JSON response. 
In that response there will be a key called "token" . 
Copy the value for that key and paste it on line marked "token" in the attached source code. 

3) Run the python file. 

     python gitable.py

"""
 
from __future__ import print_function
import urllib.request
import urllib.error
import urllib.parse
import json
import re,datetime
import sys
import csv
import random
 
class L():
  "Anonymous container"
  def __init__(i,**fields) : 
    i.override(fields)
  def override(i,d): i.__dict__.update(d); return i
  def __repr__(i):
    d = i.__dict__
    name = i.__class__.__name__
    return name+'{'+' '.join([':%s %s' % (k,pretty(d[k])) 
                     for k in i.show()])+ '}'
  def show(i):
    lst = [str(k)+" : "+str(v) for k,v in i.__dict__.items() if v != None]
    return ',\t'.join(map(str,lst))

  
def secs(d0):
  d     = datetime.datetime(*map(int, re.split('[^\d]', d0)[:-1]))
  epoch = datetime.datetime.utcfromtimestamp(0)
  delta = d - epoch
  return delta.total_seconds()
  
def anonymize_user(user_dict, user):
  if user_dict.get(user,None) == None:
    count = len(user_dict)
    user_dict[user] = 'user'+ str(count)
  return user_dict[user] 
  
def anonymize_teams(team_dict, team):
  if team_dict.get(team,None) == None:
    count = len(team_dict)
    team_dict[team] = 'team'+ str(count)
  return team_dict[team]
	
 
def dump1(u,issues):
  token = "Insert Token Here" # <===
  user_dict = {}
  request = urllib.request.Request(u, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  w = json.loads(v)
  if not w: return False
  for event in w:
    issue_id = event['issue']['number']
    # if not event.get('label'): continue
    created_at = secs(event['created_at'])
    action = event['event']
    label_name = 'no label'
    if event.get('label'): label_name = event['label']['name']
    user = anonymize_user(user_dict, event['actor']['login'])
    milestone = event['issue']['milestone']
    if milestone != None : milestone = milestone['title']
    eventObj = L(when=created_at,
                 action = action,
                 what = label_name,
                 user = user,
                 milestone = milestone)
    all_events = issues.get(issue_id)
    if not all_events: all_events = []
    all_events.append(eventObj)
    issues[issue_id] = all_events
  return True

def dump(u,issues):
  try:
    return dump1(u, issues)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False

def launchDump():
  team_id = 0
  team_list = ['SE17GroupH/Zap', 
			'syazdan25/SE17-Project',
			'rnambis/SE17-group-O', 
			'harshalgala/se17-Q', 
			'zsthampi/SE17-Group-N', 
			'karanjadhav2508/kqsse17',
			'Rushi-Bhatt/SE17-Team-K',
			'genterist/whiteWolf', 
			'SidHeg/se17-teamD', 
			'NCSU-SE-Spring-17/SE-17-S'
			]
  random.shuffle(team_list)
  for teamrepo in team_list:
    team_id = team_id + 1
    issues = dict()
    page = 1
    while(True):
      print('https://api.github.com/repos/'+teamrepo+'/issues/events?page=' + str(page))
      doNext = dump('https://api.github.com/repos/'+teamrepo+'/issues/events?page=' + str(page), issues)
      print("page "+ str(page))
      page += 1
      if not doNext : break
	
    with open('team'+str(team_id)+'.csv', 'w') as file: 
      w = csv.writer(file)
      w.writerow(["issue_id", "when", "action", "what", "user", "milestone"])
      for issue in sorted(issues.keys()):
          events = issues[issue]
          for event in events: w.writerow([issue, event.when, event.action, event.what, event.user, event.milestone])
    
    
launchDump() 
