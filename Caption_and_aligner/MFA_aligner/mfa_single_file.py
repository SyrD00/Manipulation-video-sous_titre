"""""
import subprocess
import time
from tqdm import tqdm

# Paramètres fichiers
wav_file = "C:/Users/babak/Videos/PSO/Episode/chibi_12half.wav"
txt_file ="C:/Users/babak/Videos/PSO/Episode/chibi_12half_cleaned.txt"
dict_model = "japanese_mfa"
acoustic_model = "japanese_mfa"
output_dir ="C:/Users/babak/Videos/PSO/Episode/output_align"

# Commande MFA
command = [
    "mfa", "align_one",
    wav_file,
    txt_file,
    dict_model,
    acoustic_model,
    output_dir,
    "--beam", "40"
]

# Lancer MFA dans un subprocess
print("🚀 Lancement de MFA...")
start_time = time.time()

process = subprocess.Popen(
    command,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=1
)

# Barre de progression fictive (temps estimé)
# Par défaut j'estime 100 "pas" -> tu peux adapter si tu connais la durée de traitement
total_steps = 100
pbar = tqdm(total=total_steps, desc="Alignement en cours", unit="step")

# On lit la sortie MFA ligne par ligne
for i, line in enumerate(iter(process.stdout.readline, '')):
    print(line.strip())  # affiche les logs MFA normaux
    
    # Avance fictive dans la barre
    if i < total_steps:
        pbar.update(1)

process.wait()
pbar.close()

end_time = time.time()
elapsed = end_time - start_time

print(f"/n✅ Terminé en {elapsed:.2f} secondes ({elapsed/60:.2f} minutes)")
"""


import subprocess
import time
from datetime import timedelta

# Définir la commande MFA align_one et ses arguments
# Note: N'oubliez pas d'activer votre environnement Conda au préalable
commande = [
    "mfa", "align_one", "-v",
    "C:/Users/babak/Videos/PSO/Episode/Audio/chibi_12half.wav",
    "C:/Users/babak/Videos/PSO/Episode/Txt/chibi_12half_cleaned.txt",
    "japanese_mfa",
    "japanese_mfa",
    "C:/Users/babak/Videos/PSO/Episode/output_align",
    "--beam", "50"
]

def mesurer_temps_execution(cmd):
    """
    Exécute une commande et mesure son temps d'exécution total.
    """
    print("Démarrage de l'alignement MFA...")
    temps_debut = time.time()
    
    try:
        # Exécuter la commande et attendre sa fin
        subprocess.run(cmd, check=True, capture_output=False, text=True, universal_newlines=True)
        
        temps_fin = time.time()
        temps_total_secondes = temps_fin - temps_debut
        
        # Formater le temps en minutes et secondes pour une meilleure lisibilité
        temps_total_formate = str(timedelta(seconds=int(temps_total_secondes)))
        
        print("\nAlignement terminé.")
        print(f"Temps d'exécution total : {temps_total_formate}")
        
    except FileNotFoundError:
        print("Erreur : La commande 'mfa' n'a pas été trouvée. Assurez-vous que votre environnement Conda est actif.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande : {e}")

if __name__ == "__main__":
    mesurer_temps_execution(commande)
