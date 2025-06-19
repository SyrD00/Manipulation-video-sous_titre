# extract_sub_capcut.py
import json
from typing import List, Tuple

def collect_subtitles(obj, subs: List[Tuple[int,int,str]], global_offset: int = 0):
    """
    Parcourt dicts et listes pour extraire tous les blocs de type 'subtitle'
    et calcule leurs timestamps absolus si besoin.
    """
    if isinstance(obj, dict):
        # cas d’un vrai sous-titre
        if obj.get("type") == "subtitle":
            words = obj.get("words", {})
            start = words.get("start_time")
            end   = words.get("end_time")
            text  = words.get("text") or "".join(words.get("words", []))
            if isinstance(start, int) and isinstance(end, int) and text:
                # si target_timerange existe, l’ajouter à l’offset
                tr = obj.get("segment", {}).get("target_timerange", {})
                offset = tr.get("start", 0)
                subs.append((offset + start, offset + end, text))
        # continuer le parcours
        for v in obj.values():
            collect_subtitles(v, subs, global_offset)
    elif isinstance(obj, list):
        for item in obj:
            collect_subtitles(item, subs, global_offset)

def format_srt_timestamp(ms: int) -> str:
    h = ms // 3600000
    m = (ms % 3600000) // 60000
    s = (ms % 60000) // 1000
    ms_rem = ms % 1000
    return f"{h:02}:{m:02}:{s:02},{ms_rem:03}"

def main():
    # 1) chargez votre fichier JSON CapCut
    with open("draft_content.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2) collectez tous les sous-titres
    subtitles = []
    collect_subtitles(data, subtitles)
    subtitles.sort(key=lambda x: x[0])  # trier par timecode

    # 3) écriture du .srt
    with open("output.srt", "w", encoding="utf-8") as out:
        for i, (start, end, text) in enumerate(subtitles, 1):
            out.write(f"{i}\n")
            out.write(f"{format_srt_timestamp(start)} --> {format_srt_timestamp(end)}\n")
            out.write(f"{text}\n\n")

    print(f"Fichier SRT généré avec {len(subtitles)} sous-titres.")

if __name__ == "__main__":
    main()
