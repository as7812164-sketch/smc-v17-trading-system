import tarfile
import os

workspace = r'C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system'
archive_path = os.path.join(workspace, 'hermes35_live_release.tar.gz')

files_to_pack = [
    'app.py',
    'engine/hermes30_apex_live.py',
    'engine/chart_image_generator.py',
    'alerts/telegram_service.py',
    'feed/binance_feed.py',
    'static/app.js',
    'static/mobile.html',
    'static/nexus_trade.html',
    'static/js/hermes_chart_replay.js',
    'static/js/nexus.js',
    'HERMES_3_5_SINGLE_TIER_OFFICIAL.pine'
]

with tarfile.open(archive_path, 'w:gz') as tar:
    for rel_path in files_to_pack:
        full_path = os.path.join(workspace, rel_path)
        if os.path.exists(full_path):
            tar.add(full_path, arcname=rel_path)
            print(f"Added {rel_path} ({os.path.getsize(full_path)} bytes)")
        else:
            print(f"WARNING: {rel_path} does not exist!")

print(f"Archive created at {archive_path} ({os.path.getsize(archive_path)} bytes)")
