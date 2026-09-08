import tkinter as tk
from tkinter import filedialog, messagebox
import os

def choisir_fichier(titre):
    return filedialog.askopenfilename(
        title=titre,
        filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )

root = tk.Tk()
root.withdraw()

# 1. Identifier clairement qui est qui
fichier_tb = choisir_fichier("1. Sélectionne le TXT contenant la liste des viéos TERABOX ")
if not fichier_tb: exit()

fichier_ph = choisir_fichier("2. Sélectionne le TXT contenant la liste des vidéos du TELEPHONE ")
if not fichier_ph: exit()

# 2. Lire en forçant les minuscules avec .lower() pour éviter les bugs d'extension (.MP4 vs .mp4)
with open(fichier_tb, "r", encoding="utf-8") as f:
    videos_terabox = set(line.strip().lower() for line in f if line.strip())

with open(fichier_ph, "r", encoding="utf-8") as f:
    videos_phone = set(line.strip().lower() for line in f if line.strip())

# 3. Les mathématiques des ensembles
videos_communes = videos_terabox & videos_phone
videos_orphelines = videos_terabox - videos_phone # Présentes sur TB, absentes sur le Phone

# 4. Sauvegarde des deux listes
dossier_save = filedialog.askdirectory(title="Où enregistrer les résultats ?")
if not dossier_save: exit()

chemin_communes = os.path.join(dossier_save, "liste_videos_communes.txt")
with open(chemin_communes, "w", encoding="utf-8") as f:
    for v in sorted(videos_communes):
        f.write(v + "\n")

chemin_anomalies = os.path.join(dossier_save, "liste_anomalies_videos_non_trouvees.txt")
with open(chemin_anomalies, "w", encoding="utf-8") as f:
    for v in sorted(videos_orphelines):
        f.write(v + "\n")

messagebox.showinfo(
    "Analyse terminée",
    f"Total TeraBox (unique) : {len(videos_terabox)}\n"
    f"Communes trouvées : {len(videos_communes)}\n"
    f"Anomalies (sur TB mais pas Phone) : {len(videos_orphelines)}\n\n"
    f"Regarde le fichier '2_ANOMALIES' pour comprendre pourquoi elles ne matchent pas !"
)