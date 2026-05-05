import urllib.request
import urllib.parse
import re
import html

def duckduckgo_search(query: str, max_results: int = 3) -> list:
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        
        results = []
        for match in re.finditer(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.IGNORECASE | re.DOTALL):
            url_match = match.group(1).strip()
            snippet = html.unescape(re.sub(r'<[^>]+>', '', match.group(2))).strip()
            
            if url_match.startswith("//duckduckgo.com/l/?uddg="):
                url_match = urllib.parse.unquote(url_match.split("uddg=")[1].split("&")[0])
                
            results.append({"url": url_match, "snippet": snippet})
            if len(results) >= max_results:
                break
        return results
    except Exception as e:
        print(f"Error en duckduckgo_search: {e}")
        return []

print(duckduckgo_search("latest AI news"))
