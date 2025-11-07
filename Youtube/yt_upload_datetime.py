import requests, re
from datetime import datetime
from zoneinfo import ZoneInfo

url = "https://www.youtube.com/watch?v=s5Ef1azUAcw"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}

print("Téléchargement du code source...")
html = requests.get(url, headers=headers, timeout=30).text

# Regroupe plusieurs formats possibles
patterns = [
    r'"uploadDate"\s*:\s*"([^"]+)"',
    r'<meta[^>]+itemprop=["\']uploadDate["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)["\']'
]

upload_date = None
for pat in patterns:
    m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
    if m:
        upload_date = m.group(1)
        break

if not upload_date:
    print("❌ Aucune date trouvée. (YouTube peut cacher les métadonnées si la vidéo est totalement privée ou bloquée géo.)")
else:
    print(f"✅ Date brute trouvée : {upload_date}")
    iso = upload_date.replace("Z", "+00:00")

    try:
        dt = datetime.fromisoformat(iso)
    except Exception as e:
        print("⚠️ Format ISO inattendu :", e)
    else:
        paris = dt.astimezone(ZoneInfo("Europe/Paris"))
        print("→ Heure France :", paris.strftime("%Y-%m-%d %H:%M:%S %Z"))
