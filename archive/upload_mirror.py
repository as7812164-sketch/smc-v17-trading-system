import urllib.request
import json
from pathlib import Path

url = 'https://tmpfiles.org/api/v1/upload'
filepath = Path('static/Hermes_Apex_Trading_Terminal.apk')

boundary = '----WebKitFormBoundaryHermesApexTerminal2026'
with open(filepath, 'rb') as f:
    file_bytes = f.read()

body = bytearray()
body.extend(f'--{boundary}\r\n'.encode('utf-8'))
body.extend(b'Content-Disposition: form-data; name="file"; filename="Hermes_Apex_Trading_Terminal.apk"\r\n')
body.extend(b'Content-Type: application/vnd.android.package-archive\r\n\r\n')
body.extend(file_bytes)
body.extend(f'\r\n--{boundary}--\r\n'.encode('utf-8'))

req = urllib.request.Request(
    url,
    data=bytes(body),
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': 'Mozilla/5.0'
    }
)

with urllib.request.urlopen(req, timeout=60) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    download_url = res['data']['url'].replace('tmpfiles.org/', 'tmpfiles.org/dl/')
    print('DIRECT_TMPFILES_DOWNLOAD:', download_url)
