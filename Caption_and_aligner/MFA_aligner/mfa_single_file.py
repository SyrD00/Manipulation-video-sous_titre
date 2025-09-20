"""
Ce script est l'equivalent exact de la commande MFA suivante :
mfa align <fichier_audio> <fichier_texte> <langue> <dossier_sortie> --output_format srt

"""

import os # Pour la gestion des chemins de fichiers  et vérifier leur existence.
import subprocess # Pour exécuter des commandes système (ex: mfa align).
from tqdm import tqdm # Pour afficher une barre de progression lors de l'alignement dans la console.

# Chemins à modifier
audio_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.mp3"
text_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.txt"
output_folder = "C:/Users/babak/Videos/PSO/Episode"
language = "japanese"  # changer si nécessaire

# Créer le dossier de sortie si inexistant
os.makedirs(output_folder, exist_ok=True)

# Vérifier que les fichiers existent
if not os.path.isfile(audio_file):
    print(f"❌ Fichier audio introuvable : {audio_file}")
    exit(1)
if not os.path.isfile(text_file):
    print(f"❌ Fichier texte introuvable : {text_file}")
    exit(1)

# Commande MFA

cmd = [
    "mfa", "align",
    audio_file, 
    text_file,
    language,
    output_folder,
    "--output_format", "srt"
]

# Afficher barre de progression factice pendant l'exécution
# (MFA ne renvoie pas le temps exact)
with tqdm(total=1, desc=f"Alignement {os.path.basename(audio_file)}", ncols=100) as pbar:
    subprocess.run(cmd)
    pbar.update(1)

print(f"✅ Alignement termine pour : {audio_file}")


