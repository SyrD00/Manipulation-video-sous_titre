import subprocess
import os

# ===============================
# ⚙️ CONFIGURATION UTILISATEUR
# ===============================

# 🟢 1. Chemin du fichier vidéo ou audio à traiter
input_file = r"C:\Users\babak\Videos\Precure\Dancing star precure\d.mp4"   # ← change ici ton chemin

# 🟢 2. Dossier de sortie pour les sous-titres
output_dir = r"C:\Users\babak\Videos\Precure\Dancing star precure"                   # ← change ici ton dossier

# 🟢 3. Chemin vers l’exécutable Faster-Whisper-XXL
whisper_exe = r"C:\Program Files\Whisper\Faster-Whisper-XXL\faster-whisper-xxl.exe"  # ← adapte si besoin

# ===============================
# 🚀 EXÉCUTION AUTOMATIQUE
# ===============================

# Vérifie que les chemins existent
if not os.path.exists(input_file):
    raise FileNotFoundError(f"❌ Fichier introuvable : {input_file}")

if not os.path.exists(whisper_exe):
    raise FileNotFoundError(f"❌ Exécutable introuvable : {whisper_exe}")

os.makedirs(output_dir, exist_ok=True)

# ===============================
# 🧠 Commande complète
# ===============================

cmd = [
    whisper_exe,
    input_file,
    "--task", "`transcribe",
    "--language", "ja",
    "--output_format", "srt",
    "--output_dir", output_dir,
    "--compute_type", "auto",
    "--temperature", "0",
    "--beam_size", "5",
    "--no_repeat_ngram_size", "3",
    "--condition_on_previous_text", "True",
    "--sentence",
    "--standard_asia",
    "--word_timestamps", "True",
    "--vad_filter", "True",
    "--vad_method", "silero_v5_fw",
    "--vad_threshold", "0.35",
    "--vad_min_silence_duration_ms", "100",
    "--vad_speech_pad_ms", "300",
    "--ff_rnndn_xiph",
    "--ff_lowhighpass",
    "--ff_speechnorm",
    "--ff_silence_suppress", "-50", "0.1",
    "--hallucination_silence_threshold", "4",
    "--hallucination_silence_th_temp", "0.5",
    "--print_progress",
    "--beep_off",
]


# ===============================
# ▶️ Lancement
# ===============================

print("🚀 Lancement de Faster-Whisper-XXL...\n")
process = subprocess.run(cmd, shell=True)

if process.returncode == 0:
    print(f"✅ Transcription terminée avec succès !\n➡️ Résultats dans : {output_dir}")
else:
    print(f"⚠️ Erreur (code {process.returncode}) pendant l’exécution.")
