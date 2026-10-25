import shutil
import os

base_dir = r"C:\Users\power\.gemini\antigravity\scratch\smc_v17_trading_system"
src_apk = os.path.join(base_dir, "static", "Hermes_Apex_Trading_Terminal.apk")
if not os.path.exists(src_apk):
    src_apk = os.path.join(base_dir, "HERMES 2.5 APEX Trading Terminal.apk")

dest_desktop = r"C:\Users\power\Desktop\HERMES_3.5_SINGLE_TIER_Trading_Terminal.apk"
dest_artifact = r"C:\Users\power\.gemini\antigravity\brain\53360a5d-0399-4fb3-95cf-8c5ce599d49c\HERMES_3.5_SINGLE_TIER_Trading_Terminal.apk"
dest_static = os.path.join(base_dir, "static", "HERMES_3.5_SINGLE_TIER_Trading_Terminal.apk")

print(f"Source APK exists: {os.path.exists(src_apk)}, size: {os.path.getsize(src_apk)} bytes")

shutil.copy2(src_apk, dest_desktop)
print(f"Copied to Desktop: {os.path.exists(dest_desktop)}")

shutil.copy2(src_apk, dest_artifact)
print(f"Copied to Artifact Dir: {os.path.exists(dest_artifact)}")

shutil.copy2(src_apk, dest_static)
print(f"Copied to static/: {os.path.exists(dest_static)}")
