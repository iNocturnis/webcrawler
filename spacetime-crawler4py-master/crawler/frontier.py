import os
import shelve

from threading import Thread, RLock
from queue import Queue, Empty

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
from datacollection import *


#*.ics.uci.edu/*                                                        0
#*.cs.uci.edu/*                                                         1
#*.informatics.uci.edu/*                                                2
#*.stat.uci.edu/*                                                       3
#today.uci.edu/department/information_computer_sciences/*               4

domain_semaphores = [Semaphore(3),Semaphore(3),Semaphore(3),Semaphore(3),Semaphore(3)]
data_mutex = Lock()
file_1_mutex = Lock()
file_2_mutex = Lock()
file_3_mutex = Lock()
file_4_mutex = LocK()

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
        ###CRITICAL SECTION
        data_mutex.acquire()
        try:
            return self.to_be_downloaded.pop()
        except IndexError:
            return None
        data_mutex.release()

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        ##CRITICAL SECTION
        data_mutex.acquire()
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded.append(url)
        data_mutex.release()
        ###CRITICAL SECTION
        

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)

        ##CRITICAL SECTION
        data_mutex.acquire()
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")
        self.save[urlhash] = (url, True)
        self.save.sync()
        data_mutex.release()
        ##CRITICAL SECTION


        
        # Q1
        ###CRITICAL SECTION
        file_1_mutex.acquire()
        self.uniques.add(removeFragment(url)) 

        #Writing to local file
        f = open("q1.txt", "w")
        f.write("Number of unique pages: {length}\n".format(length = len(self.uniques)))
        f.close()

        file_1_mutex.release()

        # Q2
        file_2_mutex.acquire()
        tempTok = tokenize(url)
        if len(tempTok) > self.max:
                self.max = len(tempTok)
                self.longest = url


        # creating text file for question 2
        f = open("q2.txt", "w")
        f.write("Largest page url: {url} \nLength of page: {length}".format(url = self.longest, length = self.max))
        f.close()

        file_2_mutex.release()

        # Q3
        file_3_mutex.acquire()
        tempTok = removeStopWords(tempTok)
        computeFrequencies(tempTok, self.grand_dict)

        # creating text file for question 3
        f = open("q3.txt", "w")
        sortedGrandDict = {k: v for k, v in sorted(self.grand_dict.items(), key=lambda item: item[1], reverse = True)}
        i = 0
        for k, v in sortedGrandDict.items():
            if i == 50:
                break
            else:
                f.write("{}: {}\n".format(k, v))
                i += 1
        f.close()

        file_3_mutex.release()

        # Q4
        file_4_mutex.acquire()

        fragless = removeFragment(url)
        domain = findDomains(fragless.netloc)
        if domain[1] == 'ics':
            if domain[0] not in self.ics:
                self.ics[domain[0]] = urlData(url, domain[0], domain[1])
            else:
                if fragless not in self.ics[domain[0]].getUniques():
                    self.ics[domain[0]].appendUnique(fragless)

        # creating text file for question 4
        sortedDictKeys = sorted(self.ics.keys())
        f = open("q4.txt", "w")
        for i in sortedDictKeys:
            f.write("{url}, {num}".format(url = self.ics[i].getNiceLink(), num = len(self.ics[i].getUniques())))
        f.close()
        
        file_4_mutex.release()

    def acquire_polite(url):
        return domain_semaphores[get_semaphore_index(url)].acquire()

    def release_polite(domain):
        return domain_semaphores[get_semaphore_index(url)].release()

    def get_semaphore_index(url):
        if "ics.uci.edu" in url:
            return 0
        elif "cs.uci.edu" in url:
            return 1
        elif "informatics.uci.edu" in url:
            return 2
        elif "stat.uci.edu" in url:
            return 3
        elif "today.uci.edu/department/information_computer_sciences/" in url:
            return 4
        else:
            println("ERROR")