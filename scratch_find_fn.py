import urllib.request, json
d = json.loads(urllib.request.urlopen("http://127.0.0.1:7861/config").read().decode())
for c in d["components"]:
    if c.get("type") == "textbox":
        print(f"ID: {c.get('id')}, Label: {c.get('props', {}).get('label')}")
