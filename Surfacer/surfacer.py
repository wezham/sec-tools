from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from urllib.parse import urlparse
from pyppeteer import launch
import requests
import sys
import json
import time
import socket
import argparse
import pdb
import re
import asyncio
import logging
import aiohttp
import async_timeout


total_fuzz = []

class ComparableUrl:
    def __init__(self, url):
        self.url = url
    def __eq__(self, other):
        self.url == other.url

    def __hash__(self):
        return hash(self.url)


class AssetCrawler:
    def __init__(self, starting_url, root_asset, max_crawl_count, debug, get_host, loop):
        self.starting_url = starting_url
        self.root_asset = root_asset
        self.max_crawl_count = max_crawl_count
        self.failed_to_crawl = []
        self.to_do = [starting_url]
        self.crawl_result = {}
        self.seen_list = [starting_url]
        self.hosts = {}
        self.debug = debug
        self.get_hosts = get_host
        self.loop = loop
        self.session = aiohttp.ClientSession(loop=self.loop)

    def find_forms_and_links(self, url, soup):
        forms = soup.find_all("form")
        target_json = { "forms": {}, "links": []}
        for form in forms:
            target = form.get('action')
            target_json["forms"][target] = {}
            target_json["forms"][target]["params"] = []
            target_json["forms"][target]["method"] = "GET" if not form.get('method') else form.get('method')
            inputs = form.find_all("input")
            for input in inputs:
                target_json["forms"][target]["params"].append({ "name": input.get('name'), "type": input.get("type")})

        links = soup.find_all("a")
        for link in links:
            target_json["links"].append(link.get("href"))

        try:
            self.crawl_result[url] = target_json
        except Exception:
            print(f"Failed to add target info for {url}")

        return target_json

    def clean_links(self, links, base):
        result = []
        hosts = {}
        for link in links:
            if self.debug:
                print(f"Possbily adding link {link}")
            link = self.edit_url(link, base)
            if not link or (self.root_asset not in urlparse(link).netloc or '#' in link):
                continue
            if "http" not in link:
                link = "https://" + link
            #pdb.set_trace()
            base = urlparse(link).netloc
            if self.get_hosts:
                if not base in hosts:
                    hosts[base] = socket.gethostbyname(base)

            result.append(link)
        set_result = set(result)
        list_result = list(set_result)
        if self.get_hosts:
            self.add_to_hosts(hosts)
        return list_result

    

    def add_to_hosts(self, hosts_to_add):
        for key in hosts_to_add.keys(): 
            if key not in self.hosts:
                self.hosts[key] = hosts_to_add.get(key)

    def __starts_with_slash(self, url):
        return re.match(r'^/.*', url)
    
    def __ends_with_slash(self, url):
        return re.match(r'.*/$', url) 

    def edit_url(self, url, base):
        try:
            if url and self.__starts_with_slash(url) != None:
                if self.__ends_with_slash(base):
                    replaced = url.replace("/", "")
                    url = base + replaced
                else:
                    url = base + url
        except Exception:
            print(f"Error using url: {url}, base: {base}")
        return False if not url else url

    def add_to_crawl_list(self, target_json, base_url):
        links = self.clean_links(target_json["links"], base_url)
        new_links = set([ComparableUrl(new_link) for new_link in links])
        seen_links = set([ComparableUrl(link_url2) for link_url2 in self.seen_list])
        union_list = new_links - seen_links
        self.to_do.extend([a.url for a in union_list])

    def handle_result(self, result, base_url):
        try:
            target_json = self.find_forms_and_links(url=base_url, soup=BeautifulSoup(result.content, "html.parser"))
        except Exception:
            logging.debug(f"Error extracing forms and links for {base_url}, StatusCode: {result.status_code}")
            raise
        try:
            self.add_to_crawl_list(target_json=target_json, base_url=base_url)
        except Exception:
            logging.debug(f"Error adding to crawl List for {base_url}, json is {target_json}")
            raise

    async def get(self, url):
        with async_timeout.timeout(5):
            async with self.session.get(url) as response:
                return await response.text()

    async def crawl(self, url, depth=0):
        result = await self.get(url)
        try: 
            self.handle_result(result, url)
            if depth <= self.max_crawl_count:
                await asyncio.gather([self.crawl(link, depth+1) for link in self.to_do])
        except Exception:
            logging.debug(f"Failed to crawl {url}")
            self.failed_to_crawl.append(url)
            return False

        return True

    # def initialise_crawl(self, ccount=0):
    #     if len(self.to_do) > 0 and ccount <= int(self.max_crawl_count):
    #         url = self.to_do.pop()
    #         logging.debug(f"Crawling {url}")
    #         try:
    #             base_url =  url
    #             result = requests.get(url)
    #             try:
    #                 self.handle_result(result=result, base_url=base_url)
    #             except: 
    #                 print("yas")

    #             if self.debug == True:
    #                 print("Links to Crawl:")
    #                 print("-------------------------------------------------------")
    #                 print(json.dumps(self.to_do, indent=4))
    #                 print("-------------------------------------------------------")
    #             time.sleep(1)
    #             self.initialise_crawl(ccount+1)
    #         except Exception:
    #             if self.debug == True:
    #                 print("-------------------------------------------------------")
    #                 print(f"Failed to crawl {url}")
    #                 print("-------------------------------------------------------")
    #             self.failed_to_crawl.append(url)
    #             self.initialise_crawl(ccount+1)
            
    def print_crawl_result(self):
        print("URLS:")
        print(json.dumps(self.crawl_result, indent=4))
        print("HOSTS:")
        print("-------------------------------------------------------")
        print(json.dumps(self.hosts, indent=4))

    async def get_web_page_js(self, url):
        browser = await launch()
        page = await browser.newPage()
        await page.goto(url)
        forms = await page.querySelector('form')


        dimensions = await page.evaluate('''() => {
            return {
                width: document.documentElement.clientWidth,
                height: document.documentElement.clientHeight,
                deviceScaleFactor: window.devicePixelRatio,
            }
        }''')

        print(dimensions)
        print(forms)
        # >>> {'width': 800, 'height': 600, 'deviceScaleFactor': 1}
        await browser.close()

        asyncio.get_event_loop().run_until_complete(self.get_web_page_js(url))


parser = argparse.ArgumentParser()
parser.add_argument("-gh", "--gethosts", dest = "gethosts", default = 1, help="Get hosts", type=int)
parser.add_argument("-d", "--debug", dest = "debug", default = 0, help="Debug flag", type=int)
parser.add_argument("-mc", "--maxcrawl", dest = "max", default = 5, help="Max Crawl Count", type=int)
parser.add_argument("-u", "--startingurl", dest = "url", default = "www.example.com", help="Starting URL", required=True)
parser.add_argument("-hs", "--hostname", dest = "host", default = "example", help="Root Host",required=True)
args = parser.parse_args()

print(f"Crawling from {args.url}")
print(f"Host is {args.host}")
print(f"Max Crawl count is {args.max}")
print(f"Debug Mode: {'Enabled' if args.debug else 'Disabled'}")
print(f"GetHosts: {'Enabled' if args.gethosts else 'Disabled'}")

loop = asyncio.get_event_loop()
asset_crawler = AssetCrawler(starting_url=args.url, root_asset=args.host, max_crawl_count=args.max, get_host=args.gethosts, debug=args.debug, loop=loop)
loop.run_until_complete(asset_crawler.crawl(args.url))
asset_crawler.print_crawl_result()


## TO DO: 
# Logging
# Better exception handling - shrink number of possible erros in exception blocks
#  
