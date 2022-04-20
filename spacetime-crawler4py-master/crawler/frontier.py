import os
import shelve

from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
from datacollection import *

class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config
        self.to_be_downloaded = list()
        
        # data collection is going to happen in the frontier
        # uniques encompass overall unique links
        self.uniques = set() 
        # grand_dict encompasses all the words over the entire set of links
        self.grand_dict = dict()
        # ics dict contains all subdomains of ics
        self.ics = dict()
        # used to find the longest page
        self.max = -9999
        self.longest = None
        
        if not os.path.exists(self.config.save_file) and not restart:
            # Save file does not exist, but request to load save.
            self.logger.info(
                f"Did not find save file {self.config.save_file}, "
                f"starting from seed.")
        elif os.path.exists(self.config.save_file) and restart:
            # Save file does exists, but request to start from seed.
            self.logger.info(
                f"Found save file {self.config.save_file}, deleting it.")
            os.remove(self.config.save_file)
        # Load existing save file, or create one if it does not exist.
        self.save = shelve.open(self.config.save_file)
        if restart:
            for url in self.config.seed_urls:
                self.add_url(url)
        else:
            # Set the frontier state with contents of save file.
            self._parse_save_file()
            if not self.save:
                for url in self.config.seed_urls:
                    self.add_url(url)

    def _parse_save_file(self):
        ''' This function can be overridden for alternate saving techniques. '''
        total_count = len(self.save)
        tbd_count = 0
        for url, completed in self.save.values():
            if not completed and is_valid(url):
                self.to_be_downloaded.append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        try:
            return self.to_be_downloaded.pop()
        except IndexError:
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
        
        

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")



        
        # Q1
        self.uniques.add(removeFragment(url)) 

        # Q2
        tempTok = tokenize(url)
        if len(tempTok) > self.max:
                self.max = len(tempTok)
                self.longest = url

        # Q3
        tempTok = removeStopWords(tempTok)
        computeFrequencies(tempTok, self.grand_dict)

        # Q4
        fragless = removeFragment(url)
        domain = findDomains(fragless.netloc)
        if domain[1] == 'ics':
            if domain[0] not in self.ics:
                self.ics[domain[0]] = urlData(url, domain[0], domain[1])
            else:
                if fragless not in self.ics[domain[0]].getUniques():
                    self.ics[domain[0]].appendUnique(fragless)



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
                f.write("{}: {}\n".format(k, v))
                i += 1
        f.close()

        # creating text file for question 4
        sortedDictKeys = sorted(ics.keys())
        f = open("q4.txt", "w")
        for i in sortedDictKeys:
            f.write("{url}, {num}".format(url = ics[i].getNiceLink(), num = len(ics[i].getUniques())))
        f.close()
        

        self.save[urlhash] = (url, True)
        self.save.sync()
