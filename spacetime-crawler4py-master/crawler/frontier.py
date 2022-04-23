import os
import shelve

from threading import Thread, Lock,Semaphore
from queue import Queue, Empty

import time

from utils import get_logger, get_urlhash, normalize
from scraper import is_valid
from datacollection import *


#*.ics.uci.edu/*                                                        0
#*.cs.uci.edu/*                                                         1
#*.informatics.uci.edu/*                                                2
#*.stat.uci.edu/*                                                       3
#today.uci.edu/department/information_computer_sciences/*               4



class Frontier(object):
    def __init__(self, config, restart):
        self.logger = get_logger("FRONTIER")
        self.config = config

        #Load balancer, list() 
        self.to_be_downloaded = [list(),list(),list(),list(),list()]

        self.balance_index = 0


        #Semaphore for each domain to keep each domain noice and tidy with politeness
        self.domain_semaphores = [Lock(),Lock(),Lock(),Lock(),Lock()]
        #Local data lock
        self.data_mutex = Lock()

        #FIle locks for data to make sure everything is thread-safe
        self.file_1_mutex = Lock()
        self.file_2_mutex = Lock()
        self.file_3_mutex = Lock()
        self.file_4_mutex = Lock()
        
       
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
                self.to_be_downloaded[self.get_domain_index(url)].append(url)
                tbd_count += 1
        self.logger.info(
            f"Found {tbd_count} urls to be downloaded from {total_count} "
            f"total urls discovered.")

    def get_tbd_url(self):
        ###CRITICAL SECTION
        self.data_mutex.acquire()
        try:
            initial = self.balance_index
            print("Initial " + str(initial))
            self.balance_index = self.balance_index + 1
            if self.balance_index > 4:
                    self.balance_index = 0
            while not self.to_be_downloaded[self.balance_index]:
                self.balance_index = self.balance_index + 1
                if self.balance_index > 4:
                    self.balance_index = 0
                if self.balance_index == initial:
                    self.data_mutex.release()
                    return None
            hold = self.to_be_downloaded[self.balance_index].pop()
            self.data_mutex.release()
            return hold
        except IndexError:
            self.data_mutex.release()
            return None

    def add_url(self, url):
        url = normalize(url)
        urlhash = get_urlhash(url)
        ##CRITICAL SECTION
        if urlhash not in self.save:
            self.save[urlhash] = (url, False)
            self.save.sync()
            self.to_be_downloaded[self.get_domain_index(url)].append(url)
        ###CRITICAL SECTION
        

    def mark_url_complete(self, url):
        urlhash = get_urlhash(url)

        ##CRITICAL SECTION
        if urlhash not in self.save:
            # This should not happen.
            self.logger.error(
                f"Completed url {url}, but have not seen it before.")
        self.save[urlhash] = (url, True)
        self.save.sync()
        ##CRITICAL SECTION
    

    def get_domain_index(self,url):
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
            print(url)
            print("ERROR")

        
      
    def acquire_polite(self,url):
        return self.domain_semaphores[self.get_domain_index(url)].acquire()

    def release_polite(self,url):
        return self.domain_semaphores[self.get_domain_index(url)].release()

    def acquire_data_mutex(self):
        return self.data_mutex.acquire()

    def release_data_mutex(self):
        return self.data_mutex.release()

    def acquire_234_mutex(self):
        return self.file_2_3_4_mutex.acquire()

    def release_234_mutex(self):
        return self.file_2_3_4_mutex.release()
    

    def q1(self, url):
        # rakslice (8 May 2013) Stackoverflow. https://stackoverflow.com/questions/16430258/creating-a-python-file-in-a-local-directory
        #       this saves to the local directory, so I can constantly access the right file and check if it exists or not
        path_to_script = os.path.dirname(os.path.abspath(__file__))
        my_filename = os.path.join(path_to_script, "q1.txt")
        
        # Will create a file of all the unique links and you can read the file and do lines = f.readlines() then len(lines) to get the number of unique links
        #Locking and releasing each file
        self.file_1_mutex.acquire()
        if (os.path.exists(my_filename)):
            f = open(my_filename, 'a')
            f.write(str(removeFragment(url)) + "\n")
            f.close()
        else:
            f = open(my_filename, 'w')
            f.write(str(removeFragment(url)) + "\n")
            f.close()
        self.file_1_mutex.release()

    def q234(self, url, resp):
        # rakslice (8 May 2013) Stackoverflow. https://stackoverflow.com/questions/16430258/creating-a-python-file-in-a-local-directory
        #       this saves to the local directory, so I can constantly access the right file and check if it exists or not
        
        if resp.status != 200:
            return

        tic = time.perf_counter()
        path_to_script = os.path.dirname(os.path.abspath(__file__))
        my_filename = os.path.join(path_to_script, "q2.txt")
        
        try:
            tempTok = tokenize(resp)
            self.file_2_mutex.acquire()
            if len(tempTok) > self.max:
                self.max = len(tempTok)
                self.longest = url
                f = open(my_filename, 'w')
                f.write("Longest Page: {url}, length: {length}".format(url = self.longest, length = self.max))
                f.close()
        except:
            print("resp dying for some reason ?")
        
        self.file_2_mutex.release()

        toc = time.perf_counter()
        print(f"Took {toc - tic:0.4f} seconds to save file 2 !")

        tic = time.perf_counter()
        tempTok = removeStopWords(tempTok)
        self.file_3_mutex.acquire()
        computeFrequencies(tempTok, self.grand_dict)
        # rakslice (8 May 2013) Stackoverflow. https://stackoverflow.com/questions/16430258/creating-a-python-file-in-a-local-directory
        #       this saves to the local directory, so I can constantly access the right file and check if it exists or not
        path_to_script = os.path.dirname(os.path.abspath(__file__))
        my_filename = os.path.join(path_to_script, "q3.txt")


        f = open(my_filename, "w")
        sortedGrandDict = {k: v for k, v in sorted(self.grand_dict.items(), key=lambda item: item[1], reverse = True)}
        i = 0
        for k, v in sortedGrandDict.items():
            if i == 50:
                break
            else:
                f.write("{}: {}\n".format(k, v))
                i += 1
        f.close()
        self.file_3_mutex.release()

        toc = time.perf_counter()
        print(f"Took {toc - tic:0.4f} seconds to save file 3 !")

        tic = time.perf_counter()

        fragless = removeFragment(url)
        domain = findDomains(fragless.netloc)
        self.file_4_mutex.acquire()
        if domain[1] == 'ics':
            if domain[0] not in self.ics:
                self.ics[domain[0]] = urlData(url, domain[0], domain[1])
            else:
                if fragless not in self.ics[domain[0]].getUniques():
                    self.ics[domain[0]].appendUnique(fragless)
        
        # rakslice (8 May 2013) Stackoverflow. https://stackoverflow.com/questions/16430258/creating-a-python-file-in-a-local-directory
        #       this saves to the local directory, so I can constantly access the right file and check if it exists or not
        path_to_script = os.path.dirname(os.path.abspath(__file__))
        my_filename = os.path.join(path_to_script, "q4.txt")

        # creating text file for question 4
        sortedDictKeys = sorted(self.ics.keys())
        f = open(my_filename, "w")
        for i in sortedDictKeys:
            f.write("{url}, {num}".format(url = self.ics[i].getNiceLink(), num = len(self.ics[i].getUniques())))
        f.close()
        self.file_4_mutex.release()

        toc = time.perf_counter()
        print(f"Took {toc - tic:0.4f} seconds to save file 4 !")
        