import re

import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import words
import re
import html2text
import nltk
nltk.download('stopwords')
nltk.download('words')
nltk.download('punkt')

english_words = words.words()
english_stop_words = stopwords.words('english')

# there is another nltk.download() requirement but I removed it so i forgot what it was
#       it'll show in the console/terminal if you run the code i believe
#       it showed in mine

# To explain this class I have to start by explaining the container I decided on using to keep track of subdomains of ics.uci.edu
# I decided to use a dict. Long story short, I was trying to figure out what to make my key so it would uniquely identify what I needed it to do.
#       I was going to use the parsed.netloc; however, we're taking into account that a link that looks like https://somename.vision.ics.uci.edu
#       is a unique link of the subdomain vision.
# And so I made the key the subdomain that is before ics.uci.edu in the link, and the value of the dict is this class
#       It's a very simple class, so I'm not going to commenting what it does
class urlData:
    def __init__(self, url, subdomain, domain):
        self.url = url
        self.nicelink = "http://" + removeFragment(url).netloc
        self.domain = domain
        self.subdomain = subdomain
        self.uniques = set()
        self.uniques.add(removeFragment(url))
    
    def getDomain(self):
        return self.domain
    
    def getURL(self):
        return self.url

    def getNiceLink(self):
        return self.nicelink

    def getSub(self):
        return self.subdomain
    
    def getUniques(self):
        return self.uniques

    def appendUnique(self, parse):
        self.uniques.add(parse)

# Tried to find a libary that would do this for me, but couldn't
# It parses the url and uses the netloc to separat for domain and subdomain
def findDomains(url):
    urlsplit = url.split('.')
    if urlsplit[0].lower() == 'www':
        urlsplit.remove('www')
        for i in range(len(urlsplit)):
            if urlsplit[i] == 'ics':
                if i == 0:
                    return 0, 0
                elif i == 1:
                    return urlsplit[0], urlsplit[1]
                else:
                    return urlsplit[i-1], urlsplit[i] #something like random.vision.ics.uci.edu will be consider a unique page of vision
        return None, None
    else:
        for i in range(len(urlsplit)):
            if urlsplit[i] == 'ics':
                if i == 0:
                    return 0, 0
                elif i == 1:
                    return urlsplit[0], urlsplit[1]
                else:
                    return urlsplit[i-1], urlsplit[i] #something like random.vision.ics.uci.edu will be consider a unique page of vision
        return None, None

def tokenize(url):
    # getting connection from url
    page = urllib.request.urlopen(url)
    data = page.read()
    valid = re.compile(r'[^a-zA-Z0-9]+')
    # named it tSoup for merge convience
    # need the 'lxml' parser for this.
    #       When extract_next_links is called it returns a list full of links with no resp, and I had to find a way to get text from just link.
    #       Therefore, I decided to get the plain text this way.
    tSoup = BeautifulSoup(data, 'lxml')

    # Floyd (1 March 2021) Stackoverflow. https://stackoverflow.com/questions/328356/extracting-text-from-html-file-using-python
    #       compared this with tSoup.get_text() and clean_text just provided content easier to tokenize and more inline with my intentions
    clean_text = ' '.join(tSoup.stripped_strings)
    token = word_tokenize(clean_text)

    clean_token = list()
    # This used the nltk.corpus and just removes the tokens that aren't words
    #token = [i for i in token if i.lower() in english_words]

    for word in token:
        if not valid.match(word):
            clean_token.append(word.lower())
    
    return clean_token

#added this so the scraper code is not too redundant
def computeFrequencies(tokens, d):
    for t in tokens:
        if t not in d:
            d[t] = 1
        else:
            d[t] += 1

def removeStopWords(toks):
    return [t for t in toks if t.lower() if not t.lower() in english_stop_words]
    
def removeFragment(u):
    # turn into a urlparse object
    # removed fragment in order to have "unique" links
    removefrag = urlparse(u)
    removefrag = removefrag._replace(fragment = '')
    return removefrag
