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

# Source refered - https://github.com/CSC510-2015-Axitron/project2/blob/master/gitable-sql.py
 
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
	
 
def dumpIssues2(u,issues, users):
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
    user = anonymize_user(users, event['actor']['login'])
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

def dumpIssues1(u,issues, users):
  try:
    return dumpIssues2(u, issues, users)
  except Exception as e: 
    print(e)
    print("Contact TA")
    return False
	
def dumpIssues(repo,issues,users):
  page = 1
  while(True):
    doNext = dumpIssues1('https://api.github.com/repos/'+repo+'/issues/events?page=' + str(page), issues, users)
    page += 1
    if not doNext : break
	
def dumpMilestone(repo, milestone_dict):
  page = 1
  while(page<20):
    url = 'https://api.github.com/repos/'+repo+'/milestones/' + str(page)
    print ("milestone page:"+url)
    doNext = dumpMilestone1(url, milestone_dict)
    page += 1

def dumpMilestone1(u,milestones):
  try:
    return dumpMilestone2(u, milestones)
  except urllib.request.HTTPError as e:
    if e.code == 404:
      return False
	
	
def dumpMilestone2(u, milestones):
  request = urllib.request.Request(u, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  milestone = json.loads(v)
  if not milestone or ('message' in milestone and milestone['message'] == "Not Found"): return False
  id = milestone['id']
  title = milestone['title']
  created_at = secs(milestone['created_at'])
  due_at = secs(milestone['due_on']) if milestone['due_on'] != None  else 0
  closed_at = secs(milestone['closed_at']) if milestone['closed_at'] != None else 0
    
  milestoneObj = L(id=id,
               title = title,
               created_at=created_at,
               due_at = due_at,
               closed_at = closed_at)
  milestones[id] = milestoneObj
  return True
  
def dumpComments(repo, comments,users):
  page = 1
  while(True):
    comments_url = 'https://api.github.com/repos/'+repo+'/issues/comments?page='+str(page)
    doNext = dumpComments1(comments_url, comments, token, users)
    print("comments page "+str(page))
    page += 1
    if not doNext: break

def dumpComments1(url, comments, token, users):
  try:
    request = urllib.request.Request(url, headers={"Authorization" : "token "+token})
    v = urllib.request.urlopen(request).read()
    w = json.loads(v)
    if not w:
      return False
    for comment in w:
      user = anonymize_user(users, comment['user']['login'])
      commentObj = L(ident = comment['id'],
                  issue = int((comment['issue_url'].split('/'))[-1]), 
                  user = user,
                  created_at = secs(comment['created_at']),
                  updated_at = secs(comment['updated_at']))
      comments.append(commentObj)
    return True
  except Exception as e:
    print(url)
    print(e)
    return False

def dumpCommits(repo, commits,users):
  page = 1
  while(True):
    url = 'https://api.github.com/repos/'+repo+'/commits?page=' + str(page)
    doNext = dumpCommit1(url, commits, token,users)
    print("commit page "+ str(page))
    page += 1
    if not doNext : break

def dumpCommit1(u,commits,token,users):
  request = urllib.request.Request(u, headers={"Authorization" : "token "+token})
  v = urllib.request.urlopen(request).read()
  w = json.loads(v)
  if not w: 
    return False
  for commit in w:
    user = anonymize_user(users, commit['commit']['author']['name'])
    time = secs(commit['commit']['author']['date'])
    message = commit['commit']['message']
    commitObj = L(user = user,
                time = time,
                message = message)
    commits.append(commitObj)
  return True

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
  #random.shuffle(team_list)
  
  for repo in team_list:
    team_id = team_id + 1
    issues = dict()
    milestone_dict = dict()
    comments = []
    users = dict()
    commits = []

    dumpIssues(repo,issues,users)
    with open('team'+str(team_id)+'.csv', 'w') as file: 
      w = csv.writer(file)
      w.writerow(["issue_id", "when", "action", "what", "user", "milestone"])
      for issue in sorted(issues.keys()):
          events = issues[issue]
          for event in events: w.writerow([issue, event.when, event.action, event.what, event.user, event.milestone])
    
    dumpMilestone(repo,milestone_dict)
    with open('milestone'+str(team_id)+'.csv', 'w') as file: 
      w = csv.writer(file)
      w.writerow(["milestone_id", "milestone_title", "created_at", "due_at", "closed_at"])
      for key in milestone_dict.keys():
        milestone = milestone_dict[key]
        w.writerow([milestone.id, milestone.title, milestone.created_at, milestone.due_at, milestone.closed_at])


    dumpComments(repo,comments,users)
    with open('comments'+str(team_id)+'.csv', 'w') as file:
      w = csv.writer(file)
      w.writerow(["comment_id", "issue_id", "user_id", "created_at", "updated_at"])
      for comment in comments:
        w.writerow([comment.ident, comment.issue, comment.user, comment.created_at, comment.updated_at])
    
    dumpCommits(repo, commits, users)
    with open('commits'+str(team_id)+'.csv', 'w') as file:
      w = csv.writer(file)
      w.writerow(["user_id", "time", "message"])
      for commit in commits:
        w.writerow([commit.user, commit.time, commit.message])

token = "Insert Token"
launchDump()
