"""
=============================================================

📌 UTILITÉ :
-------------
Ce script convertit les sous-titres d’un projet CapCut (fichier
draft_content.json) en un fichier standard de sous-titres .srt.
L’objectif est d’exporter automatiquement les sous-titres créés dans
CapCut tout en respectant la synchronisation exacte avec la vidéo.

📌 PRINCIPE DE FONCTIONNEMENT :
-------------------------------
1. Lecture du fichier JSON (`draft_content.json`) généré par CapCut.
2. Extraction des informations temporelles (offsets de segments) pour
   retrouver à quel moment chaque sous-titre apparaît dans la timeline.
3. Lecture des sous-titres (textes) stockés dans la section `materials`.
   - Chaque bloc de texte possède une liste de mots avec leurs
     timestamps relatifs.
   - On récupère le texte complet avec ses temps de début et fin.
4. Ajustement de la fin du sous-titre à la frame la plus proche selon
   la cadence de CapCut (30 fps).
   → Cela garantit une synchronisation frame-perfect.
5. Conversion des temps (en millisecondes) vers le format SRT standard :
   `HH:MM:SS,mmm`
6. Génération du fichier `.srt` avec les blocs numérotés.

📌 FONCTIONS PRINCIPALES :
---------------------------
- ms_to_srt_time(ms):
    Convertit un temps en millisecondes en format SRT (HH:MM:SS,mmm).

- capcut_end_align(ms):
    Aligne le temps de fin d’un sous-titre sur la frame la plus proche
    en fonction de la cadence CapCut (30 fps).

📌 STRUCTURE DU SCRIPT :
------------------------
- Paramètres (chemins du JSON source et du fichier SRT de sortie).
- Lecture et parsing du JSON.
- Étape 1 : Extraction des offsets temporels de chaque segment.
- Étape 2 : Récupération des sous-titres et application des offsets.
- Étape 3 : Conversion des temps et écriture dans un fichier `.srt`.

📌 RÉSULTAT :
-------------
Un fichier `.srt` exporté contenant les sous-titres de CapCut avec une

synchronisation fidèle à la timeline originale.


📌 Exemple simple pratique(2 lignes sous titres) :
-------------
{
  "tracks": [
    {
      "type": "text",
      "segments": [
        {
          "material_id": "txt1",
          "target_timerange": {
            "start": 0,
            "duration": 162666666
          }
        },
        {
          "material_id": "txt2",
          "target_timerange": {
            "start": 162666666,
            "duration": 111766667
          }
        }
      ]
    }
  ],
  "materials": {
    "texts": [
      {
        "id": "txt1",
        "words": {
          "start_time": [0, 414],
          "end_time": [334, 894],
          "text": ["さ", "て"]
        }
      },
      {
        "id": "txt2",
        "words": {
          "start_time": [0, 300],
          "end_time": [250, 700],
          "text": ["は", "じ"]
        }
      }
    ]
  }
}


            Étapes pour convertir manuellement en SRT
            ---------------------------------------------- 

            📌Identifier l’offset de segment
Chaque segment a un start (en microsecondes) → on convertit en millisecondes pour la SRT.
    Segment 1 : start = 0 µs → 0 ms
    Segment 2 : start = 162666666 µs → 162666 ms ≈ 162,667 s

            📌Ajouter l’offset aux temps relatifs du mot
Les temps des mots (start_time et end_time) sont relatifs au segment et souvent en ms ou µs fractionnés.

    Pour txt1 :
        Mot 1 : start = 0 + 0 = 0 ms, end = 334 ms → 00:00:00,000 → 00:00:00,334
        Mot 2 : start = 414 + 0 = 414 ms, end = 894 ms → 00:00:00,414 → 00:00:00,894

    Pour txt2 (offset 162666 ms = 162,666 s → 00:02:42,666) :
        Mot 1 : start = 0 + 162666 = 162,666 s ≈ 00:02:42,666, end = 250 + 162666 = 162,916 s ≈ 00:02:42,916
        Mot 2 : start = 300 + 162666 = 162,966 s ≈ 00:02:42,966, end = 700 + 162666 = 163,366 s ≈ 00:02:43,366

        📌Assembler le SRT
On peut soit grouper les mots d’un segment en un seul sous-titre,  :

1
00:00:00,000 --> 00:00:00,894
さて

3
00:02:42,666 --> 00:02:43,366
はじ

ou si tu veux par mot:
1
00:00:00,000 --> 00:00:00,334
さ

2
00:00:00,414 --> 00:00:00,894
て

3
00:02:42,666 --> 00:02:42,916
は

4
00:02:42,966 --> 00:02:43,366
じ
=============================================================
"""


#j'ai ecris mon propre code mais askip ce githib l'a fait aussi mas je prefere ma version:https://github.com/vogelcodes/capcut-srt-export?utm_source=chatgpt.com
import json
import math
from datetime import timedelta

# === Chemins ===
file_path = "C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0925/draft_content.json"
srt_output_path = "C:/Users/babak/Videos/PSO/1.srt"

# === Fonction ms → SRT
def ms_to_srt_time(ms):
    t = timedelta(milliseconds=ms)
    return f"{t.seconds//3600:02}:{(t.seconds//60)%60:02}:{t.seconds%60:02},{ms%1000:03}"

# === Fonction pour arrondir à la frame CapCut (30 fps)
"""
def capcut_end_align(ms):
    frame_ms = 1000 / 30  # ≈ 33.333...
    #return int(round(ms / frame_ms) * frame_ms)
    return int(math.ceil(ms / frame_ms) * frame_ms)
"""
#capcut change parfoi sa facon d'arrondri a toi d ete mettre a jour si besoin
def capcut_end_align(ms):
    frame_ms = 1000 / 30
    return int(round(ms / frame_ms) * frame_ms)

    
# === Lecture JSON
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Étape 1 : récupération des offsets temporels (start) via les segments
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

# === Étape 2 : lecture des sous-titres depuis les materials
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
        start_time = starts[0] + offset
        end_time = ends[-1] + offset
        aligned_end = capcut_end_align(end_time)
        subtitle_blocks.append({
            "start": start_time,
            "end": int(aligned_end),
            "text": ''.join(texts_list)
        })

# === Export SRT
srt_lines = []
for idx, sub in enumerate(subtitle_blocks, 1):
    srt_lines.append(str(idx))
    srt_lines.append(f"{ms_to_srt_time(sub['start'])} --> {ms_to_srt_time(sub['end'])}")
    srt_lines.append(sub['text'])
    srt_lines.append("")

with open(srt_output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(srt_lines))

print(f"✅ SRT 100% fidèle généré : {srt_output_path}")