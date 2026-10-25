import urllib.request
import json
import re

url = "https://www.youtube.com/watch?v=f18gazn0nYE"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode("utf-8", errors="ignore")

title_match = re.search(r"<title>(.*?)</title>", html)
print("TITLE:", title_match.group(1) if title_match else "None")

# Search for initial player response or ytInitialPlayerResponse
player_match = re.search(r"ytInitialPlayerResponse\s*=\s*({.+?});</script>", html)
if player_match:
    try:
        player_data = json.loads(player_match.group(1))
        video_details = player_data.get("videoDetails", {})
        print("VIDEO TITLE:", video_details.get("title"))
        print("AUTHOR:", video_details.get("author"))
        print("DESCRIPTION:", video_details.get("shortDescription")[:1000])
        print("KEYWORDS:", video_details.get("keywords"))
        
        # Check for captions
        captions = player_data.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
        print("CAPTION TRACKS:", len(captions))
        for track in captions:
            print("Track:", track.get("name"), track.get("languageCode"), track.get("baseUrl")[:100])
            # Fetch caption xml
            if track.get("baseUrl"):
                cap_req = urllib.request.Request(track.get("baseUrl"), headers={"User-Agent": "Mozilla/5.0"})
                cap_xml = urllib.request.urlopen(cap_req).read().decode("utf-8", errors="ignore")
                # Clean text from xml
                text_segments = re.findall(r'<text[^>]*>(.*?)</text>', cap_xml)
                import html as html_lib
                clean_text = [html_lib.unescape(t) for t in text_segments]
                with open("yt_transcript.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(clean_text))
                print("Transcript saved! Length lines:", len(clean_text))
                break
    except Exception as e:
        print("Error parsing player_data:", e)
else:
    print("ytInitialPlayerResponse not found")
