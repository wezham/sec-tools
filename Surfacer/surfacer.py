from bs4 import BeautifulSoup
import requests
import sys
import json
import time
from fuzzywuzzy import fuzz
from urllib.parse import urlparse
import pdb
import re

total_fuzz = []
class ComparableUrl:
    def __init__(self, url, base):
        self.url = self.edit_url(url, base)
    def __eq__(self, other):
        me = urlparse(self.url)
        other_one = urlparse(other.url)
        try:
            if self.url == "#":
                return False
            fuzz_brah = fuzz.ratio(self.url, other.url)
            total_fuzz.append(fuzz_brah)
            if fuzz_brah > 60 and root_asset in self.url:
                return True
            else:
                print(self.url)
                return False
        except:
            print("Exception")
            return True
    def __hash__(self):
        return hash(self.url)

    def edit_url(self, url, base):
        if re.match(r'^/.*', url) != None:
            if re.match(r'.*/$', base) != None and re.match(r'^/', url) != None:
                replaced = url.replace("/", "")
                url = base + replaced
            else:
                url = base + url
        return url

if len(sys.argv) == 1:
    print("Usage python surfacer.py [URL] [ROOT] [MAXCRAWLCOUNT]")
    exit()

starting_url = sys.argv[1]
root_asset = sys.argv[2]
max_crawl_count = sys.argv[3]

failed_to_crawl = []

print(f"Crawling from url {starting_url}")
seen_list = [starting_url]
to_do = seen_list
crawl_result = {}
def find_forms_and_links(soup):
    forms = soup.find_all("form")
    targets = { "forms": {}, "links": []}
    for form in forms:
        target = form.get('action')
        targets["forms"][target] = {}
        targets["forms"][target]["params"] = []
        targets["forms"][target]["method"] = "GET" if not form.get('method') else form.get('method')
        inputs = form.find_all("input")
        for input in inputs:
            targets["forms"][target]["params"].append({ "name": input.get('name'), "type": input.get("type")})

    links = soup.find_all("a")
    for link in links:
        targets["links"].append(link.get("href"))

    #print(json.dumps(targets, indent=4))
    return targets


def initialise_crawl(last_url, ccount):
    if len(to_do) > 0 and ccount <= int(max_crawl_count):
        url = to_do.pop()
        #print(f"Last URL {last_url}")
        if "http" not in url:
            url = url.replace("/", "")
            url = last_url + url
        print(f"Crawling {url}")
        try:
            result = requests.get(url)
            soup = BeautifulSoup(result.content)
            targets = find_forms_and_links(soup)
            crawl_result[url] = targets
            #print("Seen List")
            #print(json.dumps(seen_list, indent=4))
            #print("Not Seen")
            #print(json.dumps(targets["links"], indent=4))
            difference_in_found = set([ComparableUrl(link_url, url) for link_url in targets["links"]])-set([ComparableUrl(link_url, url) for link_url in seen_list])
            #print("Difference")
            #print(json.dumps([a.url for a in difference_in_found], indent=4))
            to_do.extend([a.url for a in difference_in_found])
            #print("To do")
            #print(json.dumps(to_do, indent=4))
            time.sleep(1)
            initialise_crawl(url, ccount+1)
        except:
            failed_to_crawl.append(url)
            initialise_crawl(url, ccount+1)




initialise_crawl("", 0)
print(json.dumps(crawl_result, indent=4))
print(json.dumps(total_fuzz, indent=4))
