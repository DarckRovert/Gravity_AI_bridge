import re

text = '{"fullText": "El presidente dijo \\"hola\\" ayer pero'
print("TEXT:", text)

m2 = re.search(r'"fullText"\s*:\s*"((?:[^"\\]|\\.)*?)(?:"|$)', text, re.IGNORECASE | re.DOTALL)
if m2:
    print("Match 2 (escape aware):", m2.group(1))
