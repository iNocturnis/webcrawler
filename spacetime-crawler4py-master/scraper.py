from operator import truediv
import re
from urllib import robotparser
from urllib.parse import urlparse
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup

def scraper(url, resp):
    links = extract_next_links(url, resp)
    links_valid = list()
    valid_links = open("valid_links.txt",'a')
    invalid_links = open("invalid_links.txt",'a')
    for link in links:
        if is_valid(link):
            links_valid.append(link)
            valid_links.write(link + "\n")
        else:
            invalid_links.write("From: " + url + "\n")
            invalid_links.write(link + "\n")
    return links_valid

# hopefuly fixes some loop traps and repeating (looping) directories
# the amount of repeated subdirectories allowed can be changed
# https://subscription.packtpub.com/book/big-data-and-business-intelligence/9781782164364/1/ch01lvl1sec11/crawling-your-first-website
# https://www.searchenginejournal.com/crawler-traps-causes-solutions-prevention/305781/
def is_a_loop_trap(url):
    word_dict = {}
    parsed = urlparse(url)
    url_path = str(parsed.path)
    word_list = url_path.split('/')
    for word in word_list:
        if word in word_dict:
            word_dict[word] += 1
            if word_dict[word] == 3:
                return True
        else:
            word_dict[word] = 1
    return False

# Tests to see if the url is ok to be crawled by checking against the robots.txt
# file. It does so by checking the URL or URL prefixes and will return true if page is allowed to be crawled
# https://docs.python.org/3/library/urllib.robotparser.html#urllib.robotparser.RobotFileParser
# http://pymotw.com/2/robotparser/
def robots_ok(baseurl):
    eva = robotparser.RobotFileParser()
    rooturl = str(urljoin(baseurl, '/')[:-1])   # get each subdomain by itself
    eva.set_url(rooturl + "/robots.txt")         # set location of robots.txt 
    eva.read()                                  # read and fead to parser
    return eva.can_fetch('*', baseurl)          # returns true if useragent is allowed to crawl

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    pages = list()
    if resp.status == 200:
        #do stuff
        soup = BeautifulSoup(resp.raw_response.content)
        tempFile = open("test6.txt", 'a')
        #Getting all the links, href = true means at least theres a href value, dont know what it is yet
        for link in soup.find_all('a', href=True):
            #There is a lot of relative paths stuff here gotta add them
            href_link = link.get('href')

            #Relative path
            ##Suprisingly index fail safe
            #some <a href> give //thenlink.com...
            if href_link.startswith("//"):
                href_link = href_link[2:]
            
            #Relative path fixing
            if(href_link.startswith("/")):
                href_link = urljoin(url,href_link)

            #skipping query with specific actions which mutate the websites and cause a trap
            if "do=" in href_link:
                continue

            tempFile.write(href_link + "\n")
            #Adding to the boi wonder pages
            pages.append(href_link)
    else:
        print("Page error !")
    return pages

#*.ics.uci.edu/*
#*.cs.uci.edu/*
#*.informatics.uci.edu/*
#*.stat.uci.edu/*
#today.uci.edu/department/information_computer_sciences/*

def is_valid(url):


    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.

    try:
        #Gotta check if they are in the domain
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        elif re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$",parsed.path.lower()):
            return False
        elif not re.match(
            r".*ics.uci.edu/.*"
            + r"|.*cs.uci.edu/.*"
            + r"|.*informatics.uci.edu/.*"
            + r"|.*stat.uci.edu/.*"
            + r"|today.uci.edu/department/information_computer_sciences/.*",url):
            return False
        elif parsed.fragment:
            return False
        elif is_a_loop_trap(url):
            return False
        elif not robots_ok(url):
            return False
        else:
            return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
