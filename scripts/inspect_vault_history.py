import urllib.request
import json
import base64

token = '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'

def get_vault_at_commit(sha):
    try:
        url = f'https://api.github.com/repos/as7812164-sketch/smc-ai-agent/contents/vault_state.json?ref={sha}'
        req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'Hermes-Vault'})
        with urllib.request.urlopen(req) as resp:
            content = json.loads(resp.read().decode())['content']
            data = json.loads(base64.b64decode(content).decode('utf-8'))
            accs = data.get('accounts', [])
            tot_bal = sum(a.get('current_balance', 0.0) for a in accs[:10])
            all_bal = sum(a.get('current_balance', 0.0) for a in accs)
            print(f"Commit {sha[:8]} | Sections 1-10 Bal: ${tot_bal:.2f} | Total All Accounts: ${all_bal:.2f} | Accs count: {len(accs)}")
            return data
    except Exception as e:
        print(f"Error {sha[:8]}: {e}")
        return None

# Get list of commits over time
url = 'https://api.github.com/repos/as7812164-sketch/smc-ai-agent/commits?sha=data-vault&per_page=100'
req = urllib.request.Request(url, headers={'Authorization': f'token {token}', 'User-Agent': 'Hermes-Vault'})
with urllib.request.urlopen(req) as resp:
    commits = json.loads(resp.read().decode())

print("Analyzing last 100 commits on data-vault:")
for i in [0, 10, 25, 50, 75, 99]:
    if i < len(commits):
        c = commits[i]
        sha = c['sha']
        msg = c['commit']['message']
        date = c['commit']['committer']['date']
        print(f"\n--- Index {i} ({date}) Message: {msg} ---")
        get_vault_at_commit(sha)
