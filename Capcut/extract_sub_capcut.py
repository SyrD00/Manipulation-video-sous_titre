#voir plsu detail sur l'explication de ce script ici :https://chatgpt.com/s/t_68751a9063f48191a42b4b2af88cc54a
import json
import math
from datetime import timedelta

# === Chemins ===
file_path = "C:/Users/babak/AppData/Local/CapCut/User Data/Projects/com.lveditor.draft/0832/draft_content.json"
srt_output_path = "C:/Users/babak/Videos/PSO/Fight Might Me!.srt"

# === Fonction ms → SRT
def ms_to_srt_time(ms):
    t = timedelta(milliseconds=ms)
    return f"{t.seconds//3600:02}:{(t.seconds//60)%60:02}:{t.seconds%60:02},{ms%1000:03}"

# === Fonction pour arrondir à la frame CapCut (30 fps)
def capcut_end_align(ms):
    frame_ms = 1000 / 30  # ≈ 33.333...
    #return int(round(ms / frame_ms) * frame_ms)
    return int(math.ceil(ms / frame_ms) * frame_ms)
    
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