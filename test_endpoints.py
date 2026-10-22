import urllib.request
import urllib.error
import json
import time

url_geo = "http://127.0.0.1:7860/v1/tiktok/geo?user=jorgeluisvilxhez"
url_osint = "http://127.0.0.1:7860/v1/tiktok/deep_osint?user=jorgeluisvilxhez"

def test_endpoint(url):
    print(f"Testing {url} ...")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            print(f"[{resp.status}] OK. Response size: {len(data)} bytes")
            # attempt to parse json
            parsed = json.loads(data)
            print("Keys:", list(parsed.keys()))
            if "error" in parsed:
                print("ERROR key found in response:", parsed["error"])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"Error: {e}")

# Wait for server to boot
time.sleep(5)
test_endpoint(url_geo)
print("-" * 50)
test_endpoint(url_osint)
