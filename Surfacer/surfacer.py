from bs4 import BeautifulSoup
import requests
import sys
import json
import time
from fuzzywuzzy import fuzz
from urllib.parse import urlparse
import pdb

class ComparableUrl:
    def __init__(self, url):
        self.url = url
    def __eq__(self, other):
        pdb.set_trace()
        me = urlparse(self.url)
        other_one = url_parse(other.url)
        try:
            if fuzz.ratio(me.geturl(), other_one.geturl()) > 1 and fuzz.ratio(starting_url, me.get_url()) > 1:
                return True
            else:
                return False
        except:
            print("Exception")
            return True
    def __hash__(self):
        return hash(self.url)

if len(sys.argv) == 1:
    print("Usage python surfacer.py [URL] [MAXCRAWLCOUNT]")
    exit()

starting_url = sys.argv[1]
max_crawl_count = sys.argv[2]
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
            difference_in_found = set([ComparableUrl(url) for url in targets["links"]])-set([ComparableUrl(url) for url in seen_list])
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
