import re
from urllib import robotparser
from bs4 import BeautifulSoup
from collections import defaultdict
import requests

# Tests to see if the url is ok to be crawled by checking against the robots.txt
# file. return true if page is allowed to be crawled, returns true if not robots file, and false otherwise
# https://docs.python.org/3/library/urllib.robotparser.html#urllib.robotparser.RobotFileParser
# http://pymotw.com/2/robotparser/
# https://stackoverflow.com/questions/43085744/parsing-robots-txt-in-python
robots_seen = dict() # all robots go here (global so we can store over all site)
def robots_ok(parsed)->bool:
    global robots_seen                                  # global dict for files
    robots_seen[parsed.netloc] = False                  # default seen
    try:
        url = 'http://' + parsed.netloc + '/robots.txt' # filter url and set
        sitemap = requests.get(url)                     # sitmap get
        if sitemap.status_code != 200:                  # no file so let her rip
            return True
        eva = robotparser.RobotFileParser(url)          
        eva.read()
        if eva.can_fetch('*', url):                     # if eva can see url add to dict
            robots_seen[parsed.netloc] = True
        return robots_seen[parsed.netloc]               # the dict 
    except:
        return False                                    # default
# check if the site is in the dict if not run it into the dict
def robots_are_ok(parsed):
    global robots_seen
    if parsed.netloc not in robots_seen: # if not in dict run check site
        return robots_ok(parsed)
    else:
        return robots_seen[parsed.netloc] # if it has been read return its value
                                            