import zipfile
import re

for apk_path in ['HERMES 2.5 APEX Trading Terminal.apk', 'static/Hermes_Apex_Trading_Terminal.apk']:
    print('=== Checking:', apk_path)
    try:
        with zipfile.ZipFile(apk_path, 'r') as z:
            manifest_data = z.read('AndroidManifest.xml')
            print('Manifest size:', len(manifest_data))
            # Find package name or strings in manifest
            strings = re.findall(b'[a-zA-Z0-9_\\.]{4,}', manifest_data)
            print('Sample manifest tokens:', [s.decode('latin1') for s in strings[:15]])
            
            # Check classes.dex
            dex_data = z.read('classes.dex')
            print('DEX size:', len(dex_data))
            urls = re.findall(rb'https?://[^\x00\s\"\'<>]+', dex_data)
            for u in set(urls):
                s = u.decode('latin1', errors='ignore')
                if not any(x in s for x in ['schemas.android', 'w3.org', 'google', 'android.com']):
                    print('App URL:', s)
    except Exception as e:
        print('Error:', e)
