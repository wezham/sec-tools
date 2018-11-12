from bs4 import BeautifulSoup
import requests
import sys
import json
import time
import socket
from fuzzywuzzy import fuzz
from urllib.parse import urlparse
import pdb
import re

total_fuzz = []

class ComparableUrl:
    def __init__(self, url):
        self.url = url
    def __eq__(self, other):
        self.url == other.url

    def __ne__(self, other):
        return (self.url != other.url) or (self.url != other.url)

    def __hash__(self):
        return hash(self.url)


if len(sys.argv) == 1:
    print("Usage python surfacer.py [URL] [ROOT] [MAXCRAWLCOUNT]")
    exit()

class AssetCrawler:
    def __init__(self, starting_url, root_asset, max_crawl_count, debug):
        self.starting_url = starting_url
        self.root_asset = root_asset
        self.max_crawl_count = max_crawl_count
        self.failed_to_crawl = []
        self.to_do = [starting_url]
        self.crawl_result = {}
        self.seen_list = [starting_url]
        self.hosts = {}
        self.debug = debug

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
        except:
            print(f"Failed to add target info for {url}")

        return target_json

    def clean_links(self, links, base):
        result = []
        hosts = {}
        for link in links:
            link = self.edit_url(link, base)
            if self.root_asset not in link or '#' in link:
                continue
            if "http" not in link:
                link = "https://" + link
            base = urlparse(link).netloc
            if not base in hosts:
                hosts[base] = socket.gethostbyname(base)

            result.append(link)
        set_result = set(result)
        list_result = list(set_result)
        self.add_to_hosts(hosts)
        return list_result

    def add_to_hosts(self, hosts_to_add):
        for key in hosts_to_add.keys(): 
            if key not in self.hosts:
                self.hosts[key] = hosts_to_add.get(key)

    def edit_url(self, url, base):
        try:
            if re.match(r'^/.*', url) != None:
                if re.match(r'.*/$', base) != None and re.match(r'^/', url) != None:
                    replaced = url.replace("/", "")
                    url = base + replaced
                else:
                    url = base + url
        except:
            print(f"Error using url: {url}, base: {base}")
        return url

    def add_to_crawl_list(self, target_json, base_url):
        links = self.clean_links(target_json["links"], base_url)
        new_links = set([ComparableUrl(new_link) for new_link in links])
        seen_links = set([ComparableUrl(link_url2) for link_url2 in self.seen_list])
        union_list = new_links - seen_links
        self.to_do.extend([a.url for a in union_list])

    def initialise_crawl(self, last_url, ccount):
        if len(self.to_do) > 0 and ccount <= int(self.max_crawl_count):
            url = self.to_do.pop()
            #print(f"Last URL {last_url}")
            if "http" not in url:
                url = url.replace("/", "")
                url = last_url + url
            if self.debug == True:
                print("-------------------------------------------------------")
                print(f"Crawling {url}")
                print("-------------------------------------------------------")
            try:
                base_url =  url
                result = requests.get(url)
                soup = BeautifulSoup(result.content)
                target_json = self.find_forms_and_links(url=url, soup=soup)
                self.add_to_crawl_list(target_json=target_json, base_url=base_url)
                if self.debug == True:
                    print("Links to Crawl:")
                    print("-------------------------------------------------------")
                    print(json.dumps(self.to_do, indent=4))
                    print("-------------------------------------------------------")
                time.sleep(1)
                self.initialise_crawl(url, ccount+1)
            except:
                if self.debug == True:
                    print("-------------------------------------------------------")
                    print(f"Failed to crawl {url}")
                    print("-------------------------------------------------------")
                self.failed_to_crawl.append(url)
                self.initialise_crawl(url, ccount+1)
            
    def print_crawl_result(self):
        print("URLS:")
        print(json.dumps(self.crawl_result, indent=4))
        print("HOSTS:")
        print("-------------------------------------------------------")
        print(json.dumps(self.hosts, indent=4))

for i in range(1,5):
    if not sys.argv[i]:
        print("python surfacer.py [STARTING_URL] [ROOT_HOST] [MAX_CRAWL] [DEBUG]")
        exit()

starting_url = sys.argv[1]
root_asset = sys.argv[2]
max_crawl = sys.argv[3]
debug = True if int(sys.argv[4]) else False 
print(f"Crawling from {starting_url}")
print(f"Host is {root_asset}")
print(f"Max Crawl count is {max_crawl}")
print(f"Debug Mode: {'Enabled' if debug else 'Disabled'}")
assetCrawler = AssetCrawler(starting_url=starting_url, root_asset=root_asset, max_crawl_count=max_crawl, debug=debug)
assetCrawler.initialise_crawl("", 0)
assetCrawler.print_crawl_result()

# if sys.argv.get(1, "NEIN") == "NEIN" or
