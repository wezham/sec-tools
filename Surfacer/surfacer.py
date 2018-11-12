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

def clean_links(links, base):
    result = []
    for link in links:
        link = edit_url(link, base)
        if root_asset not in link or '#' in link:
            continue
        result.append(link)
    set_result = set(result)
    list_result = list(set_result)
    return list_result

def edit_url(url, base):
    try:
        if re.match(r'^/.*', url) != None:
            if re.match(r'.*/$', base) != None and re.match(r'^/', url) != None:
                replaced = url.replace("/", "")
                url = base + replaced
            else:
                url = base + url
    except:
        print("GIANT FUCKUP")
    return url

def initialise_crawl(last_url, ccount):
    if len(to_do) > 0 and ccount <= int(max_crawl_count):
        url = to_do.pop()
        #print(f"Last URL {last_url}")
        if "http" not in url:
            url = url.replace("/", "")
            url = last_url + url
        print(f"Crawling {url}")
        try:
            global base_url
            base_url =  url
            result = requests.get(url)
            soup = BeautifulSoup(result.content)
            targets = find_forms_and_links(soup)
            crawl_result[url] = targets
            links = clean_links(targets["links"], base_url)
            new_links = set([ComparableUrl(new_link) for new_link in links])
            seen_links = set([ComparableUrl(link_url2) for link_url2 in seen_list])
            union_list = new_links - seen_links
            to_do.extend([a.url for a in union_list])
            print("To do")
            print(json.dumps(to_do, indent=4))
            time.sleep(1)
            initialise_crawl(url, ccount+1)
        except:
            failed_to_crawl.append(url)
            initialise_crawl(url, ccount+1)

initialise_crawl("", 0)
print(json.dumps(crawl_result, indent=4))
print(json.dumps(total_fuzz, indent=4))
