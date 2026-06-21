import urllib.request, json, urllib.error
url = "https://integrate.api.nvidia.com/v1/chat/completions"
data = json.dumps({"model":"meta/llama3-70b-instruct", "messages":[{"role":"user", "content":"Hi"}], "max_tokens":10}).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Authorization': 'Bearer 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', 'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as res:
        print("Success:", res.read().decode())
except urllib.error.HTTPError as e:
    print("Error:", e.code, e.read().decode())
