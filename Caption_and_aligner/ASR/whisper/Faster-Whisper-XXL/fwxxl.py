import subprocess
import os
import shutil

# ===============================
# ⚙️ CONFIGURATION UTILISATEUR
# ===============================

# 🟢 1. Chemin du fichier vidéo ou audio à traiter
input_file = r"C:\Users\babak\Music\VideoProc Converter AI\cure connect.mp3"   # ← change ici ton chemin

# 🟢 2. Dossier de sortie pour les sous-titres
output_dir = r"C:\Users\babak\Documents\Transcriptions"                # ← change ici ton dossier

#🟢 3. Chemin vers l’exécutable Faster-Whisper-XXL si pas dans le Path
#whisper_exe = r"C:\Program Files\Whisper\Faster-Whisper-XXL\faster-whisper-xxl.exe"  # ← adapte si besoin

whisper_exe = "faster-whisper-xxl.exe"  # Si l’exécutable est dans le Path système
# ===============================
# 🚀 EXÉCUTION AUTOMATIQUE
# ===============================

# Vérifie que les chemins existent
if not os.path.exists(input_file):
    raise FileNotFoundError(f"❌ Fichier introuvable : {input_file}")

# Vérifie dans le répertoire courant OU dans le PATH
if not (os.path.exists(whisper_exe) or shutil.which(whisper_exe)):
    raise FileNotFoundError(f"❌ Exécutable introuvable : {whisper_exe}")


os.makedirs(output_dir, exist_ok=True)

# ===============================
# 🧠 Commande complète
# ===============================
'''
faster-whisper-xxl.exe `
  --model large-v3-turbo `
  --language ja `
  --japanese blend `
  --output_format srt `
  --output_dir "C:/Users/babak/Documents/Transcriptions" `
  --vad_filter True `
  --vad_method silero_v4_fw `
  --vad_min_silence_duration_ms 100 `
  --vad_speech_pad_ms 200 `
  --sentence `
  --standard_asia `
  --max_line_width 16 `
  --max_line_count 2 `
  --max_gap 0.5 `
  --word_timestamps True `
  --ignore_dupe_prompt 2 `
  --hallucination_silence_threshold 4 `
  --v3_offsets_off `
  "C:/Users/babak/Music/VideoProc Converter AI/cure connect.mp3"

'''


cmd = [
    whisper_exe,
    "--model", "large-v3-turbo",
    "--language", "ja",
    "--output_format", "srt",
    "--output_dir", output_dir,
    "--vad_method", "silero_v5_fw",
    "--vad_threshold", "0.4",
    "--vad_min_silence_duration_ms", "100",
    input_file
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
