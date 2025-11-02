
from faster_whisper import WhisperModel
from tqdm import tqdm
import os
import time

# Chemin audio/video
audio_path = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.mp4"
txt_path = os.path.splitext(audio_path)[0] + ".txt"

# Charger le modèle
model = WhisperModel("medium", device="cpu", compute_type="int8")

# Transcrire
segments, info = model.transcribe(audio_path, task="transcribe")

total_duration = info.duration  # durée totale en secondes

# Écrire le texte complet avec barre de progression basée sur la durée
with open(txt_path, "w", encoding="utf-8") as f:
    progress_bar = tqdm(total=total_duration, desc="📝 Transcription", unit="sec", ncols=100)
    current_time = 0.0
    start_time = time.time()

    for segment in segments:
        # Écrire le texte
        f.write(segment.text + " ")

        # Calculer l'avancement en fonction du temps écoulé de l'audio
        progress_bar.update(segment.end - current_time)
        current_time = segment.end

        # Optionnel : afficher la vitesse de transcription (x temps réel)
        elapsed = time.time() - start_time
        speed = current_time / elapsed if elapsed > 0 else 0
        progress_bar.set_postfix_str(f"{speed:.2f}x")

    progress_bar.close()

print(f"✅ Transcription sauvegardée dans : {txt_path}")


