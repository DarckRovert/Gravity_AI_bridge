import urllib.request, urllib.error
req = urllib.request.Request('https://integrate.api.nvidia.com/v1/models', headers={'Authorization': 'Bearer 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'})
try:
    res = urllib.request.urlopen(req)
    print('OK:', res.read().decode()[:100])
except urllib.error.HTTPError as e:
    print('ERROR:', e.code, e.read().decode())
