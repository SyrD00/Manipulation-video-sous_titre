
"""
====================================================
 Script : capcut_to_llc.py

 Pré requis :fais tes split dans capcut
====================================================
 Qu'est-ce qu'un fichier LLC ? https://filext.com/fr/extension-de-fichier/LLC
Les fichiers LLC appartiennent principalement à LosslessCut. Les fichiers LLC peuvent désigner deux types de 
fichiers distincts servant à des usages différents.
Fichier de projet Lossless Cut : 
Ce fichier contient des listes de coupes et des marqueurs de timeline pour monter des vidéos sans perte de
 qualité. Il stocke généralement les instructions de montage dans un format texte brut, souvent basé sur JSON. 
 Ouvrez-le avec le logiciel LosslessCut de lwks.com.

 
 Utilité :
     Ce script convertit un projet CapCut (draft_content.json)
     en un fichier .llc compatible avec LosslessCut.
     Le fichier .llc peut ensuite être importé dans LosslessCut
     pour retrouver les mêmes découpes (splits) que dans CapCut.

 Fonctionnement :
 1. CapCut enregistre les temps des segments vidéo (splits)
    dans le JSON `draft_content.json`, en microsecondes.
 2. Le script lit ce fichier, extrait tous les segments vidéo,
    convertit les temps en secondes décimales (format LosslessCut).
 3. Le résultat est exporté dans un fichier `export.llc`.

 Entrées :
     - draft_content.json (exporté depuis CapCut)

 Sorties :
     - export.llc (à ouvrir dans LosslessCut)

 Exemple d’utilisation :
     1. Place ce script et `draft_content.json` dans le même dossier.
     2. Exécute le script :
         python capcut_to_llc.py
     3. Le fichier `export.llc` sera généré et prêt à être importé
        dans LosslessCut.

 Remarque :
     - Le premier segment n’a que `end`.
     - Les segments suivants ont `start` + `end`.
     - Les temps sont en secondes décimales (float).
====================================================
"""
import json

capcut_json_file = "C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0322/draft_content.json"
output_llc_file = r"C:\Users\babak\Downloads\47_cut.llc"

# === Lecture du JSON CapCut ===
with open(capcut_json_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# === Récupération du vrai nom de la vidéo ===
media_filename = "video.mp4"  # valeur par défaut
videos = data.get("materials", {}).get("videos", [])
if videos:
    # Prendre le champ "material_name" de la première vidéo
    media_filename = videos[0].get("material_name", media_filename)

# === Extraction des segments de découpe ===
cut_segments = []
for track in data.get("tracks", []):
    if track.get("type") == "video":
        for i, seg in enumerate(track.get("segments", [])):
            timerange = seg.get("target_timerange", {})
            start_us = timerange.get("start", 0)
            duration_us = timerange.get("duration", 0)

            start_s = start_us / 1e6
            end_s = (start_us + duration_us) / 1e6

            segment_dict = {"name": ""}
            if i != 0:
                segment_dict["start"] = start_s
            segment_dict["end"] = end_s
            cut_segments.append(segment_dict)

# === Construire le fichier LLC ===
llc_data = {
    "version": 1,
    "mediaFileName": media_filename,
    "cutSegments": cut_segments
}

# === Exporter ===
with open(output_llc_file, "w", encoding="utf-8") as f:
    json.dump(llc_data, f, indent=2)

print(f"✅ Fichier .llc généré : {output_llc_file} avec {len(cut_segments)} splits")
print(f"🎬 Nom de la vidéo détecté : {media_filename}")
