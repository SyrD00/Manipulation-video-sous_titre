#pip install -U git+https://github.com/m-bain/whisperX.git

import whisperx
from whisperx.utils import read_srt, write_srt

# === 🔧 CONFIGURATION ===
video_file = r"C:\Users\babak\Videos\Precure\Dancing star precure\D2.mp4"          # ta vidéo source
input_srt = r"C:\Users\babak\Videos\Precure\Dancing star precure\DSP.srt"        # ton fichier SRT existant (ex. Whisper Large)
output_srt = r"C:\Users\babak\Videos\Precure\Dancing star precure\DSP_align.srt"        # sortie recalée
language = "ja"                   # langue (ja, en, fr, etc.)
device = "cpu"                   # ou "cpu" si pas de GPU


# === 1️⃣ Charger le SRT existant ===
segments = read_srt(input_srt)
print(f"Nombre de segments lus : {len(segments)}")


# === 2️⃣ Charger le modèle d'alignement ===
align_model, metadata = whisperx.load_align_model(language_code=language, device=device)


# === 3️⃣ Réaligner le texte sur la vidéo (WhisperX extrait l’audio automatiquement) ===
aligned = whisperx.align(segments, align_model, metadata, video_file, device=device)


# === 4️⃣ Écrire le nouveau SRT ===
whisperx.utils.write_srt(aligned["segments"], output_srt)
print(f"✅ Fichier réaligné enregistré : {output_srt}")
