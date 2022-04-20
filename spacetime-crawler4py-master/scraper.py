import re
import urllib.request
from urllib.parse import urlparse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.corpus import words
import html2text
import nltk
#moved all my code to a separted py file and imported it here
from datacollection import *

# nltk.download('stopwords')
# nltk.download('words')
# there is another nltk.download() requirement but I removed it so i forgot what it was
#       it'll show in the console/terminal if you run the code i believe. it appeared in mine

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

    # Needs to be moved
    # creating text file that includes the number of unique links
    f = open("q1.txt", "w")
    f.write("Number of unique pages: {length}\n".format(length = len(uniques)))
    f.close()

    # creating text file for question 2
    f = open("q2.txt", "w")
    f.write("Largest page url: {url} \nLength of page: {length}".format(url = longest, length = max))
    f.close()

    # creating text file for question 3
    f = open("q3.txt", "w")
    sortedGrandDict = {k: v for k, v in sorted(grand_dict.items(), key=lambda item: item[1], reverse = True)}
    i = 0
    for k, v in sortedGrandDict.items():
        if i == 50:
            break
        else:
            f.write(k, ':', v, '\n')
            i += 1
    f.close()

    # creating text file for question 4
    sortedDictKeys = sorted(ics.keys())
    f = open("q4.txt", "w")
    for i in sortedDictKeys:
        f.write("{url}, {num}".format(url = ics[i].getNiceLink(), num = len(ics[i].getUniques())))
    f.close()

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
        else:
            return True

    except TypeError:
        print ("TypeError for ", parsed)
        raise
