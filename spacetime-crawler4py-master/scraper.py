from distutils.filelist import findall
from operator import truediv
import re
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from robotsokay import *

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

            # don't know if this is too expensive, otherwise idk
            # takes parsed url and if not ok on robots goes next, else we can write file    
            parsed = urlparse(href_link)    
            if not robots_are_ok(parsed):
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
        url_parsed_path = parsed.path.lower()   # this may help speed things up a little bit (less calls to parsed.path)
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
        # https://support.archive-it.org/hc/en-us/articles/208332963-Modify-crawl-scope-with-a-Regular-Expression
        # length check for looping filters and queries (could add hash check for similarity or regex, but don't know if we want to as this works well enought)
        # we can adjust it based on what the cralwer does as well
        if len(url) > 169:
            return False
        # this fixes any search box that keeps going page to page, currenty allow a depth of 2 filters 
        if re.match(r".*(&filter%.*){3,}",url_parsed_path):
            return False
        # this is for urls which when opened, download a file (do we want to download these files and tokenize them)
        # elif re.match(r"^.*\&format=(\D{3,4})\Z$",url_parsed_path):
        #     return False
        # another looping directory check but more advanced than the one contained in is_a_trap
        if re.match(r"^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$",url_parsed_path):
            return False
        # extra directories check (we can add as we find)
        if re.match(r"^.*(/misc|/sites|/all|/themes|/modules|/profiles|/css|/field|/node|/theme){3}.*$", url_parsed_path):
            return False
        # calendar checks plus adding or downloading calendar (ical)
        if re.match(r"^.*calendar.*$",url_parsed_path):
            return False
        if parsed.query.find('ical') != -1:
            return False 
        else:
            return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
