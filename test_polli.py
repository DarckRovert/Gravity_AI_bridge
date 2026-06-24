import urllib.request
import urllib.parse

prompt = "majestic ruins of Machu Picchu"
encoded = urllib.parse.quote(prompt)

url = (
    f"https://image.pollinations.ai/prompt/{encoded}?width=1280&height=720&nologo=true"
)
print("Testing:", url)
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp:
        print("Success!", len(resp.read()))
except Exception as e:
    print("Error:", e)
