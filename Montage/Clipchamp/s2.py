from pyannote.audio.pipelines import SpeechTextAlignment
from pyannote.core import Segment
import ffmpeg
import pysubs2
import os

# ==========
# ⚙️ CONFIG
# ==========
input_video     = r"C:/Users/babak/Videos/PSO/Video/PSO24/14.mp4"
input_srt       = r"C:/Users/babak/Downloads/14.srt"
output_srt      = r"C:/Users/babak/Downloads/14_pyannote_aligned.srt"

# ==========
# 🎵 Convertir en WAV 16kHz mono
# ==========
wav_file = "tmp_audio.wav"
(
    ffmpeg
    .input(input_video)
    .output(wav_file, ac=1, ar=16000, format="wav", loglevel="quiet")
    .overwrite_output()
    .run()
)
print(f"✅ Audio converti : {wav_file}")

# ==========
# 🧩 Charger pipeline Pyannote
# ==========
pipeline = SpeechTextAlignment(language="ja")

# ==========
# 📜 Charger ton texte
# ==========
subs = pysubs2.load(input_srt, encoding="utf-8")

# ==========
# 🔁 Alignement segment par segment
# ==========
aligned_subs = pysubs2.SSAFile()
for i, line in enumerate(subs, 1):
    text = line.text.strip()
    if not text:
        continue
    segment = Segment(line.start / 1000, line.end / 1000)

    try:
        aligned = pipeline(wav_file, text, segment=segment)
        start, end = aligned["segment"].start, aligned["segment"].end
        aligned_subs.append(
            pysubs2.SSAEvent(start=int(start * 1000),
                             end=int(end * 1000),
                             text=text)
        )
        print(f"[{i:03d}] {start:.3f} → {end:.3f} | {text}")
    except Exception as e:
        print(f"⚠️ Ligne {i} non alignée : {e}")
        aligned_subs.append(line)

# ==========
# 💾 Sauvegarde finale
# ==========
aligned_subs.save(output_srt, encoding="utf-8")
print(f"\n✅ Fichier aligné : {output_srt}")

# Nettoyage
if os.path.exists(wav_file):
    os.remove(wav_file)
