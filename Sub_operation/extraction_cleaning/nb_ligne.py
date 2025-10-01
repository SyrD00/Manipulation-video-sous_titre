

# Nom du fichier texte à analyser
fichier = "C:/Users/babak/Videos/PSO/Episode/temp/PSO23.txt"

# Ouvre le fichier en lecture et compte les lignes
with open(fichier, "r", encoding="utf-8") as f:
    nb_lignes = sum(1 for _ in f)

print(f"Le fichier '{fichier}' contient {nb_lignes} lignes.")
