
"""
=============================================================
📌 Script : extract_segments_sub.py
=============================================================

UTILITÉ :
---------
Ce script extrait et exporte les sous-titres d’un projet CapCut
(`draft_content.json`) en les découpant par segments vidéo.
Chaque segment de la vidéo correspondra à un fichier sous-titre 
et un fichier texte séparé.si tu veux que le txt met en commentaire la partie srt

RÉSULTAT :
----------
- Pour chaque segment vidéo → un fichier `.srt` (sous-titres horodatés).
- Pour chaque segment vidéo → un fichier `.txt` (texte brut concaténé).
- Tous les fichiers sont exportés dans le dossier spécifié (`output_dir`).

FONCTIONNEMENT :
----------------
1. Lecture du fichier `draft_content.json` de CapCut.
2. Extraction des segments vidéo (start et end en microsecondes).
3. Extraction des sous-titres (`materials.texts`) avec leurs temps
   relatifs et application de l’offset segment.
4. Alignement des temps de fin sur la frame CapCut (30 fps).
5. Attribution des sous-titres à leur segment vidéo respectif.
6. Export :
   - `.srt` → format standard compatible VLC, YouTube, etc.
   - `.txt` → uniquement le texte concaténé pour chaque segment.

FORMATS TEMPORELS :
-------------------
- CapCut stocke les temps en microsecondes (µs).
- Conversion en millisecondes (ms) pour le SRT.
- Format SRT : `HH:MM:SS,mmm`

EXEMPLE DE SORTIE :
-------------------
Segment_01.srt :
----------------
1
00:00:00,000 --> 00:00:02,500
Bonjour à tous

2
00:00:02,600 --> 00:00:05,000
Bienvenue dans la vidéo

Segment_01.txt :
----------------
Bonjour à tous 
Bienvenue dans la vidéo

=============================================================
"""



import json
import math
import os
from datetime import timedelta

# === Chemins ===
file_path = "C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0925/draft_content.json"
output_dir = "C:/Users/babak/Videos/PSO/Episode/Split_txt_aud"
os.makedirs(output_dir, exist_ok=True)

# === Fonctions ===
def ms_to_srt_time(ms):
    t = timedelta(milliseconds=ms)
    hours, remainder = divmod(t.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = ms % 1000
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

def capcut_end_align(ms):
    frame_ms = 1000 / 30
    return int(round(ms / frame_ms) * frame_ms)


# === Lecture JSON ===
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Étape 1 : récupérer les segments vidéo (µs) ===
video_segments = []
for track in data.get("tracks", []):
    if track.get("type") == "video":
        for seg in track.get("segments", []):
            tr = seg.get("target_timerange", {})
            start = tr.get("start", 0)
            end = start + tr.get("duration", 0)
            video_segments.append((start, end))

# === Étape 2 : récupérer les offsets des textes ===
material_start_times = {}
for track in data.get("tracks", []):
    if track.get("type") == "text":
        for seg in track.get("segments", []):
            mat_id = seg.get("material_id")
            timerange = seg.get("target_timerange", {})
            start_offset = timerange.get("start")
            if mat_id and start_offset is not None:
                material_start_times[mat_id] = start_offset

# === Étape 3 : récupérer sous-titres absolus avec fin alignée frame ===
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

    starts = words["start_time"]
    ends = words["end_time"]
    texts_list = words["text"]

    if len(starts) == len(ends) == len(texts_list):
        start_abs = offset + starts[0]
        end_abs = offset + ends[-1]
        aligned_end = capcut_end_align(end_abs)
        subtitle_blocks.append({
            "start": start_abs,
            "end": aligned_end,
            "text": ''.join(texts_list)
        })

# === Étape 4 : associer chaque sous-titre à son segment et exporter SRT + TXT ===
for idx, (seg_start, seg_end) in enumerate(video_segments, start=1):
    seg_subs = [s for s in subtitle_blocks if s['start'] >= seg_start and s['end'] <= seg_end]

    # --- SRT ---
    """
    srt_lines = []
    for i, sub in enumerate(seg_subs, start=1):
        start_srt = ms_to_srt_time(sub["start"])
        end_srt = ms_to_srt_time(sub["end"])
        srt_lines.append(f"{i}")
        srt_lines.append(f"{start_srt} --> {end_srt}")
        srt_lines.append(sub["text"])
        srt_lines.append("")
    srt_filename = os.path.join(output_dir, f"segment_{idx:02}.srt")
    with open(srt_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    """
    
    # --- TXT ---
    texts_concat = "\n".join([s['text'] for s in seg_subs])
    #txt_filename = os.path.join(output_dir, f"segment_{idx:02}.txt")
    #nommer les segments par 1,2,3,..
    txt_filename = os.path.join(output_dir, f"{idx}.txt")
    with open(txt_filename, "w", encoding="utf-8") as f:
        f.write(texts_concat)

    # --- Affichage console ---
    print(f"Segment {idx} ({ms_to_srt_time(seg_start)}-{ms_to_srt_time(seg_end)}) → {len(seg_subs)} sous-titres")
    print(f"Texte : {texts_concat}\n")

print(f"\n✅ Tous les SRT et TXT exportés dans : {output_dir}")
