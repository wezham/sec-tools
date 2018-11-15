# sec-tools
Tools for security related things 

## What is in this so far 

### Email Permutor 

This tool is for generating permutations of email addresses. The aim to have an email fuzzer. Give a company name, first name and last name. It will find out the email address of the company 

### Asset Surfacer

Give this python tool a URL and a limit. It will crawl this url and subsequent pages looking for forms, get paramters, and links and when it completes its crawl return back a JSON report of URLS, forms, paramters and there types, destinations, get paramters. This is to plot attack surface 

usage: surfacer.py [-h] [-gh GETHOSTS] [-d DEBUG] [-mc MAX] -u URL -hs HOST


Features:

1. Returns a JSON blob of 
```
targets = {
  "sampleurl": {
    "forms": {
            "/docs/search": {
                "params": [
                    {
                        "name": "q",
                        "type": "search"
                    }
                ],
                "method": "get"
            }
     },
     "links": [
            "/docs",
            "/docs/sms",
            "/docs/voice",
            "/docs/runtime",
            "/docs/chat",
            "/docs/studio",
            "/docs/all",
            "/docs/libraries",
            "https://support.twilio.com/hc/en-us",
            "/docs/search",
            "/login",
            "/try-twilio",
            "#",
            "/docs/sms",
            "/docs/voice",
            "/docs/runtime",
            "/docs/chat",
            "/docs/studio",
            "/docs/all",
            "/docs/libraries",
            "https://support.twilio.com/hc/en-us",
            "#",
            "#"
        ]
  }
}

hosts: {
  "URL1": "127.0.0.1",
  "URL2": "127.0.0.2"
}
```
TO-DO:

1. Map open ports for hosts 
2. Javascript application scraping (implement puppetter python libary ) 
3. Threading for workload perf improvements 
4. Extracting get paramters 
5. Smart extraction on paramters with interesting names ( url, ip, etc ) i.e. can we make signatures 
