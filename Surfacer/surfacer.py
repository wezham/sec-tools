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
        self.to_do = []
        self.crawl_result = {}
        self.seen_list = {starting_url}
        self.hosts = {}
        self.debug = debug
        self.get_hosts = get_host
        self.loop = loop

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
            link = self.clean_link(link=link.get("href"), base=url)
            target_json["links"].append(link) if link else False 

        try:
            self.crawl_result[url] = target_json
        except Exception:
            print(f"Failed to add target info for {url}")

        return target_json

    def clean_link(self, link, base):
        link = self.edit_url(link, base)

        if not link or (self.root_asset not in urlparse(link).netloc or '#' in link):
            return False
    
        parsed = urlparse(link)
        parsed_link = parsed.netloc
        path = parsed.path if parsed.path else ""
        return_link = "https://" + parsed_link + path

        if self.get_hosts:
            if not parsed_link in self.hosts:
                try:
                    self.hosts[parsed_link] = socket.gethostbyname(parsed_link)
                except Exception:
                    print(f"Error with hosts for {parsed_link}")

        return return_link

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
        pdb.set_trace()
        new_links = set([new_link for new_link in target_json["links"]])
        seen_links = self.seen_list
        union_list = new_links - seen_links
        return union_list

    def handle_result(self, result, base_url):
        try:
            target_json = self.find_forms_and_links(url=base_url, soup=BeautifulSoup(result, "html.parser"))
        except Exception:
           print(f"Error extracing forms and links for {base_url}")
           raise
        try:
            return self.add_to_crawl_list(target_json=target_json, base_url=base_url)
        except Exception:
            print(f"Error adding to crawl List for {base_url}, json is {target_json}")
            raise

    async def get(self, url):
        response = await self.session.get(url, ssl=False)
        return await response.text()

    async def crawl(self, url, depth=0):
        print(f"Actually crawling {url}")
        print(f"Depth {depth}")
        time.sleep(1)
        self.seen_list.add(url)
        res = await self.get(url)
        try: 
            pdb.set_trace()
            to_do = self.handle_result(res, url)
        except Exception:
           print(f"Failed to crawl {url}")
           self.failed_to_crawl.append(url)
           return False
        else:
            if depth <= self.max_crawl_count:
                await asyncio.gather( *([self.crawl(link, depth+index) for index, link in enumerate(to_do) ]) )

       

    def get_item(self, item):
        return item

    async def main(self, url):
        async with aiohttp.ClientSession(loop=self.loop) as session:
            self.session = session
            result = await self.crawl(url)
            return result

    def print_crawl_result(self):
        print("URLS:")
        json.dumps(self.crawl_result, indent=4)
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
loop.run_until_complete(asset_crawler.main(args.url))
asset_crawler.print_crawl_result()


## TO DO: 
# Logging
# Better exception handling - shrink number of possible erros in exception blocks
#  
