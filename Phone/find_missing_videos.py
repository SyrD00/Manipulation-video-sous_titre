import tkinter as tk
from tkinter import filedialog, messagebox


def choisir_fichier(titre):
    return filedialog.askopenfilename(
        title=titre,
        filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
    )


# Créer la fenêtre
root = tk.Tk()
root.withdraw()

# Choisir list_video_terabox.txt
fichier_terabox = choisir_fichier(
    "Sélectionne list_video_terabox.txt"
)

if not fichier_terabox:
    exit()

# Choisir list_video_phone.txt
fichier_phone = choisir_fichier(
    "Sélectionne list_video_phone.txt"
)

if not fichier_phone:
    exit()

# Lire les vidéos de Terabox
with open(fichier_terabox, "r", encoding="utf-8") as f:
    videos_terabox = set(line.strip() for line in f if line.strip())

# Lire les vidéos du téléphone
with open(fichier_phone, "r", encoding="utf-8") as f:
    videos_phone = [line.strip() for line in f if line.strip()]

# Garder uniquement les vidéos du téléphone absentes de Terabox
videos_manquantes = [
    video for video in videos_phone
    if video not in videos_terabox
]

# Choisir où enregistrer le résultat
fichier_sortie = filedialog.asksaveasfilename(
    title="Enregistrer la liste des vidéos manquantes",
    defaultextension=".txt",
    initialfile="videos_manquantes.txt",
    filetypes=[("Fichiers texte", "*.txt")]
)

if not fichier_sortie:
    exit()

# Écrire le résultat
with open(fichier_sortie, "w", encoding="utf-8") as f:
    for video in videos_manquantes:
        f.write(video + "\n")

messagebox.showinfo(
    "Terminé",
    f"{len(videos_manquantes)} vidéos ont été trouvées.\n\n"
    f"Résultat enregistré dans :\n{fichier_sortie}"
)