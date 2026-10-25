import urllib.request
import urllib.error
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_endpoint(url):
    print(f"\nTesting: {url}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            status = resp.status
            content = resp.read()
            print(f"Status: {status}, Length: {len(content)} bytes")
            if 'json' in resp.headers.get('Content-Type', ''):
                try:
                    data = json.loads(content.decode('utf-8'))
                    print(f"JSON Keys/Summary: {list(data.keys()) if isinstance(data, dict) else len(data)}")
                except Exception as e:
                    print(f"JSON parse error: {e}")
            else:
                print(f"Content snippet: {content[:120]}")
            return status, content
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        return e.code, None
    except Exception as e:
        print(f"Connection Failed: {e}")
        return None, None

print("=== CHECKING LOCALHOST:8000 ===")
test_endpoint("http://localhost:8000/trade")
test_endpoint("http://localhost:8000/api/trade/positions")
test_endpoint("http://localhost:8000/api/deca/summary")

print("\n=== CHECKING PRODUCTION (RENDER) ===")
test_endpoint("https://smc-ai-agent.onrender.com/trade")
test_endpoint("https://smc-ai-agent.onrender.com/api/trade/positions")
test_endpoint("https://smc-ai-agent.onrender.com/api/deca/summary")
