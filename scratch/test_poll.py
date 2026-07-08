import urllib.request, urllib.error
req = urllib.request.Request('https://image.pollinations.ai/prompt/a%20cute%20cat', headers={'User-Agent': 'Mozilla/5.0'})
try:
    data = urllib.request.urlopen(req).read()
    print("SUCCESS", len(data))
except urllib.error.HTTPError as e:
    print("ERROR", e.code, e.reason)
