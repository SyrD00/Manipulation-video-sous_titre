"""NB Apres avoir teste whisper_timestamped, je recommande d'utiliser whisperx qui est
  plus précis pour la génération de sous-titres avec horodatage.
  whisper_timestamped est vraiment mauvais sur les timings ,je l'ai testé
  
 """
#version CLI executable
import subprocess

cmd = [
    "whisper_timestamped",
    "C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav",
    "--language", "ja",
    "--output_dir", "C:/Users/babak/Videos/PSO/Episode/Audio/",
    "--punctuations_with_words", "True",
    "--compute_confidence", "True"
]
subprocess.run(cmd)

"""


hyper lent pour charger model a voir

import whisper_timestamped as whisper

# Charger le modèle
model = whisper.load_model("large")

# Charger l'audio
audio = whisper.load_audio("C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav")

# Transcrire
result = whisper.transcribe(
    model,
    audio,
    language="ja",
    beam_size=5,
    best_of=5,
    temperature=(0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    vad=True,
    detect_disfluencies=False,
    compute_word_confidence=True
)

# Sauvegarder uniquement le SRT
with open("C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.srt", "w", encoding="utf-8") as f:
    whisper.utils.write_srt(result["segments"], f)

print("✅ SRT généré uniquement !")



"""
