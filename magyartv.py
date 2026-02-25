import os
import re
import time
import threading
import requests
import socket
from flask import Flask, Response, request, redirect

app = Flask(__name__)

# --- AUTOMATIKUS IP CÍM KERESÉS ---
def get_local_ip():
    try:
        # Megpróbáljuk kitalálni a gép valódi belső IP címét
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

# --- BEÁLLÍTÁSOK ---
# Ha a docker-compose-ban nincs megadva HOST_IP, akkor automatikusan kitalálja
HOST_IP = os.environ.get("HOST_IP", get_local_ip())

# FIGYELEM: A Dockerfile WORKDIR beállítása miatt ezek az útvonalak fixek!
# Itt van az átírás, amit kerestél:
SHOWS_FILE = "/magyartv/config/shows.txt"
VOD_DIR = "/magyartv/vod_output"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://mediaklikk.hu/',
    'Accept-Language': 'hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7'
}

# Élő csatornák listája
CHANNELS = {
    "m1": ("mtv1live", "M1 HD"),
    "m2": ("mtv2live", "M2 HD"),
    "m4": ("mtv4live", "M4 Sport HD"),
    "m4sportplusz": ("mtv4pluszlive", "M4 Sport+ HD"),
    "m5": ("mtv5live", "M5 HD"),
    "duna": ("dunalive", "Duna HD"),
    "dunaworld": ("dunaworldlive", "Duna World HD")
}

# --- 1. ÉLŐ TV (M3U GENERÁTOR) ---
@app.route('/m3u')
def generate_m3u():
    print("--- M3U lista generálása ---", flush=True)
    m3u = "#EXTM3U\n"
    for cid, (video_id, name) in CHANNELS.items():
        try:
            player_url = f"https://player.mediaklikk.hu/playernew/player.php?video={video_id}"
            resp = requests.get(player_url, headers=HEADERS, timeout=10)
            match = re.search(r'"file"\s*:\s*"([^"]+m3u8[^"]*)"', resp.text)
            if match:
                stream_url = match.group(1).replace('\\/', '/')
                if stream_url.startswith('//'):
                    stream_url = 'https:' + stream_url
                m3u += f'#EXTINF:-1 tvg-id="{cid}" group-title="Magyar TV", {name}\n{stream_url}\n'
        except Exception as e:
            print(f"Hiba a(z) {name} csatornánál: {e}", flush=True)
    return Response(m3u, mimetype='text/plain')

# --- 2. VISSZANÉZŐ (VOD) ÁTIRÁNYÍTÓ ---
@app.route('/vod')
def get_vod():
    url = request.args.get('url')
    print(f"--- VOD kérés érkezett: {url} ---", flush=True)
    if not url: return "Nincs URL", 400

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        article_text = resp.text

        # VIDEO ID KERESÉSE (BŐVÍTETT LISTA)
        video_id = None
        patterns = [
            r'player\.php\?video=([^"&\'\\]+)',   # URL-ben lévő ID
            r'common_video_id\s*=\s*\'([^\']+)\'', # Gyakori változó
            r'"video"\s*:\s*"([^"]+)"',           # JSON konfig
            r'video:\s*\'([^\']+)\'',             # JS változó
            r'data-video="([^"]+)"',              # HTML attribútum
            r'"token"\s*:\s*"([^"]+)"'            # Token alapú azonosítás
        ]

        for p in patterns:
            match = re.search(p, article_text)
            if match:
                video_id = match.group(1)
                break

        if video_id:
            print(f"Azonosító megtalálva: {video_id[:30]}...", flush=True)
            player_url = f"https://player.mediaklikk.hu/playernew/player.php?video={video_id}"
            player_resp = requests.get(player_url, headers=HEADERS, timeout=15)
            
            # STREAM LINK KERESÉSE
            s_match = re.search(r'"file"\s*:\s*"([^"]+m3u8[^"]*)"', player_resp.text) or \
                      re.search(r'file\s*:\s*\'([^\']+m3u8[^\']*)\'', player_resp.text)

            if s_match:
                stream_url = s_match.group(1).replace('\\/', '/')
                if stream_url.startswith('//'): stream_url = 'https:' + stream_url
                print(f"SIKER: Stream link továbbítva.", flush=True)
                return redirect(stream_url)
            else:
                print("HIBA: Nincs m3u8 link a lejátszóban.", flush=True)
        else:
            print(f"HIBA: Nem található Video ID. HTML hossza: {len(article_text)}", flush=True)

        return "Nem sikerült kinyerni a videó linkjét.", 404

    except Exception as e:
        print(f"KRITIKUS HIBA: {e}", flush=True)
        return str(e), 500

# --- 3. AUTOMATIKUS EPIZÓD-KERESŐ ROBOT ---
def sync_vods_job():
    while True:
        if os.path.exists(SHOWS_FILE):
            print("VOD Szinkronizáció indítása...", flush=True)
            try:
                with open(SHOWS_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "," not in line: continue
                        name, url = line.strip().split(',', 1)
                        folder = os.path.join(VOD_DIR, name.strip())
                        os.makedirs(folder, exist_ok=True)
                        
                        try:
                            resp = requests.get(url.strip(), headers=HEADERS, timeout=15)
                            links = re.findall(r'href="([^"]+/video/(\d{4})/(\d{2})/(\d{2})/[^"]+)"', resp.text)
                            
                            count = 0
                            for link_data in set(links):
                                full_url = "https://mediaklikk.hu" + link_data[0] if not link_data[0].startswith("http") else link_data[0]
                                f_name = f"{name.strip()} - {link_data[1]}-{link_data[2]}-{link_data[3]}.strm"
                                f_path = os.path.join(folder, f_name)
                                
                                if not os.path.exists(f_path):
                                    with open(f_path, "w", encoding="utf-8") as sf:
                                        sf.write(f"http://{HOST_IP}:8000/vod?url={full_url}")
                                    count += 1
                            if count > 0:
                                print(f"  -> {name.strip()}: {count} új epizód.", flush=True)
                        except Exception as e:
                            print(f"  -> Hiba a {name.strip()} feldolgozásakor: {e}", flush=True)

            except Exception as e:
                print(f"Hiba a robot futásakor: {e}", flush=True)
            print("Szinkronizáció kész. Alvás 12 óráig...", flush=True)
        else:
            print(f"VÁRAKOZÁS: A {SHOWS_FILE} fájl nem található!", flush=True)
        
        time.sleep(43200)

if __name__ == '__main__':
    threading.Thread(target=sync_vods_job, daemon=True).start()
    app.run(host='0.0.0.0', port=8000)
