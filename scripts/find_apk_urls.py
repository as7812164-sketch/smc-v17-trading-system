import zipfile
import re

with zipfile.ZipFile('static/Hermes_Apex_Trading_Terminal.apk', 'r') as z:
    for n in z.namelist():
        if 'string' in n.lower() or n.endswith('.arsc') or 'res/' in n:
            data = z.read(n)
            # Find any URLs or domain names
            matches = re.findall(b'https?://[a-zA-Z0-9\\.\\-_/:]+', data)
            for m in set(matches):
                print(n, '->', m.decode('latin1'))
