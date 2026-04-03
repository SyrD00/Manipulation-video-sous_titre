import subprocess
import os
import shutil

# ===============================
# ⚙️ CONFIGURATION UTILISATEUR
# ===============================
# 🟢 1. Chemin du fichier vidéo ou audio à traiter
input_file = r"C:\Users\babak\Downloads\Naviyu.mp4"   # ← change ici ton chemin

# 🟢 2. Dossier de sortie pour les sous-titres
output_dir = r"C:\Users\babak\Downloads"                # ← change ici ton dossier

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

#"--vad_threshold", "0.4",

""" 
Paramètres recommandés pour la musiquue :
1. Désactiver ou assouplir le VAD

--vad_filter "True" est ton plus grand ennemi pour les chansons. Il essaie de supprimer tout ce qui n'est pas de la parole 
# claire. En musique, il confond souvent le chant avec les instruments et coupe la séquence.


2. Désactiver le mode "Batched"
Le mode --batched est rapide, mais il segmente l'audio de manière rigide. Pour de la musique où les phrases s'étirent
 (vibrato, notes longues), le mode classique (non-batched) est souvent plus précis pour ne pas couper un mot en deux.
"""
cmd = [
    whisper_exe,
    input_file,
    "--model", "large-v3-turbo",
    "--language", "ja",
    "--japanese", "blend",
    "--output_format", "srt",
    "--output_dir", output_dir,
    
    "--vad_method", "pyannote_onnx_v3",
    "--vad_threshold", "0.1",
    "--max_gap", "0.1",
    "--vad_speech_pad_ms", "200",
    "--sentence",
    "--standard_asia",
    "--word_timestamps", "True",
    "--ignore_dupe_prompt", "2",
    "--v3_offsets_off",
    "--threads", "4",
    "--print_progress",
    
    
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
