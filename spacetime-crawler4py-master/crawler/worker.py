from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests from scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            start = time.perf_counter()
            tic = time.perf_counter()
            tbd_url = self.frontier.get_tbd_url()
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to get_tbd_url")
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            self.frontier.acquire_polite(tbd_url)
            tic = time.perf_counter()
            resp = download(tbd_url, self.config, self.logger)
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do download url")

            tic = time.perf_counter()
            self.frontier.q1(tbd_url)
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do log q1 url")
            
            tic = time.perf_counter()
            self.frontier.q234(tbd_url, resp)
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do log q234 url")

            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            
            tic = time.perf_counter()
            scraped_urls = scraper.scraper(tbd_url, resp)
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do scrape url")
            
            
            tic = time.perf_counter()
            self.frontier.acquire_data_mutex()
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.release_data_mutex()
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do add_url stuffs")

            tic = time.perf_counter()
            self.frontier.mark_url_complete(tbd_url)
            toc = time.perf_counter()
            print(f"Took {toc - tic:0.4f} seconds to do store stuffs")
            
            while start + self.config.time_delay > time.perf_counter():
                time.sleep(self.config.time_delay/5)
            self.frontier.release_polite(tbd_url)            
