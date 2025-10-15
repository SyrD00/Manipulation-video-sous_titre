import json

# === Chemins ===
file_path = "C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0832/draft_content.json"
# Nouveau chemin pour le fichier .txt
txt_output_path = "C:/Users/babak/Videos/PSO/Fight Might Me!.txt"

# === Lecture JSON ===
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Étape 1 : récupération des offsets temporels (start) via les segments ===
material_start_times = {}
tracks = data.get("tracks", [])
for track in tracks:
    if track.get("type") == "text":
        for seg in track.get("segments", []):
            mat_id = seg.get("material_id")
            timerange = seg.get("target_timerange", {})
            start_offset = timerange.get("start")
            if mat_id and start_offset is not None:
                material_start_times[mat_id] = start_offset // 1000  # µs → ms

# === Étape 2 : lecture des sous-titres depuis les materials ===
texts = data.get("materials", {}).get("texts", [])
subtitle_blocks = []

for text in texts:
    mat_id = text.get("id")
    words = text.get("words")
    if not mat_id or not isinstance(words, dict):
        continue
    if not all(k in words for k in ["start_time", "end_time", "text"]):
        continue
    offset = material_start_times.get(mat_id)
    if offset is None:
        continue

    texts_list = words["text"]
    if texts_list:
        subtitle_blocks.append({
            "text": ''.join(texts_list)
        })

# === Export TXT ===
# Création d'une liste contenant uniquement le texte des sous-titres
txt_lines = [sub['text'] for sub in subtitle_blocks]

# Écriture du contenu dans le nouveau fichier .txt
with open(txt_output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(txt_lines))

print(f"✅ Fichier texte généré : {txt_output_path}")